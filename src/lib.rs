//! Rust core of gen_example_env: .env parsing and .env.example rendering.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

const SECRET_WORDS: [&str; 8] = [
    "SECRET", "TOKEN", "PASSWORD", "PASSWD", "PRIVATE", "CREDENTIAL", "AUTH", "API",
];

/// One line of a .env file, preserving enough to re-emit it faithfully.
#[pyclass(frozen, get_all, module = "gen_example_env._core")]
struct Line {
    raw: String,
    key: Option<String>,
    value: Option<String>,
    export: bool,
    quoted: bool,
    comment: String,
}

#[pymethods]
impl Line {
    #[new]
    #[pyo3(signature = (raw, key=None, value=None, export=false, quoted=false, comment=String::new()))]
    fn new(
        raw: String,
        key: Option<String>,
        value: Option<String>,
        export: bool,
        quoted: bool,
        comment: String,
    ) -> Self {
        Self { raw, key, value, export, quoted, comment }
    }

    #[getter]
    fn is_assignment(&self) -> bool {
        self.key.is_some()
    }
}

#[derive(Clone, Copy)]
enum Mode {
    Blank,
    Placeholder,
    KeepSafe,
}

impl Mode {
    fn parse(s: &str) -> PyResult<Self> {
        match s {
            "blank" => Ok(Self::Blank),
            "placeholder" => Ok(Self::Placeholder),
            "keep-safe" => Ok(Self::KeepSafe),
            _ => Err(PyValueError::new_err(format!("unknown mode: {s:?}"))),
        }
    }
}

/// Same line boundaries as Python's `str.splitlines()`.
fn splitlines(text: &str) -> Vec<&str> {
    let mut out = Vec::new();
    let mut start = 0;
    let mut chars = text.char_indices().peekable();
    while let Some((i, c)) = chars.next() {
        if matches!(
            c,
            '\n' | '\r' | '\x0b' | '\x0c' | '\x1c' | '\x1d' | '\x1e' | '\u{85}' | '\u{2028}' | '\u{2029}'
        ) {
            out.push(&text[start..i]);
            start = i + c.len_utf8();
            if c == '\r' && matches!(chars.peek(), Some(&(_, '\n'))) {
                chars.next();
                start += 1;
            }
        }
    }
    if start < text.len() {
        out.push(&text[start..]);
    }
    out
}

/// Match `[A-Za-z_][A-Za-z0-9_]*\s*=` and return (key, text after '=').
fn parse_key(s: &str) -> Option<(&str, &str)> {
    let first = s.chars().next()?;
    if !(first.is_ascii_alphabetic() || first == '_') {
        return None;
    }
    let end = s
        .find(|c: char| !(c.is_ascii_alphanumeric() || c == '_'))
        .unwrap_or(s.len());
    let rest = s[end..].trim_start().strip_prefix('=')?;
    Some((&s[..end], rest))
}

/// Split the text after `=` into (value, quoted, trailing_comment).
fn split_value(rest: &str) -> (&str, bool, &str) {
    let s = rest.trim_start();
    if let Some(quote) = s.chars().next().filter(|c| *c == '\'' || *c == '"') {
        let bytes = s.as_bytes();
        let mut end = s[1..].find(quote).map(|i| i + 1);
        while let Some(e) = end {
            if bytes[e - 1] != b'\\' {
                break;
            }
            end = s[e + 1..].find(quote).map(|i| i + e + 1);
        }
        if let Some(e) = end {
            let tail = s[e + 1..].trim();
            let comment = if tail.starts_with('#') { tail } else { "" };
            return (&s[1..e], true, comment);
        }
    }
    // Unquoted: an inline comment starts at whitespace followed by '#'.
    let mut it = s.char_indices().peekable();
    while let Some((i, c)) = it.next() {
        if c.is_whitespace() && matches!(it.peek(), Some(&(_, '#'))) {
            return (s[..i].trim_end(), false, s[i..].trim());
        }
    }
    (s.trim(), false, "")
}

fn parse_line(raw: &str) -> Line {
    let plain = |raw: &str| Line {
        raw: raw.to_owned(),
        key: None,
        value: None,
        export: false,
        quoted: false,
        comment: String::new(),
    };
    let s = raw.trim();
    if s.is_empty() || s.starts_with('#') {
        return plain(raw);
    }
    let body = raw.trim_start();
    let exported = body
        .strip_prefix("export")
        .filter(|r| r.starts_with(char::is_whitespace))
        .and_then(|r| parse_key(r.trim_start()));
    let (export, found) = match exported {
        Some(f) => (true, Some(f)),
        None => (false, parse_key(body)),
    };
    let Some((key, rest)) = found else { return plain(raw) };
    let (value, quoted, comment) = split_value(rest);
    Line {
        raw: raw.to_owned(),
        key: Some(key.to_owned()),
        value: Some(value.to_owned()),
        export,
        quoted,
        comment: comment.to_owned(),
    }
}

fn key_looks_secret(key: &str) -> bool {
    let up = key.to_ascii_uppercase();
    up.contains("KEY") || SECRET_WORDS.iter().any(|w| up.contains(w))
}

fn render(lines: &[&Line], mode: Mode) -> String {
    let mut out = String::new();
    for line in lines {
        match &line.key {
            None => out.push_str(&line.raw),
            Some(key) => {
                if line.export {
                    out.push_str("export ");
                }
                out.push_str(key);
                out.push('=');
                match mode {
                    Mode::Blank => {}
                    Mode::Placeholder => {
                        out.push('<');
                        out.push_str(key);
                        out.push('>');
                    }
                    Mode::KeepSafe => {
                        if !(line.quoted || key_looks_secret(key)) {
                            out.push_str(line.value.as_deref().unwrap_or(""));
                        }
                    }
                }
                if !line.comment.is_empty() {
                    out.push_str("  ");
                    out.push_str(&line.comment);
                }
            }
        }
        out.push('\n');
    }
    out
}

#[pymodule]
mod _core {
    use super::*;

    #[pymodule_export]
    use super::Line;

    /// Parse `text` into `Line` objects, one per input line, in order.
    #[pyfunction]
    fn parse_env_lines(text: &str) -> Vec<Line> {
        splitlines(text).into_iter().map(parse_line).collect()
    }

    /// Heuristic: quoted values or keys with secret-ish names are treated as secrets.
    #[pyfunction]
    fn looks_secret(line: &Line) -> PyResult<bool> {
        let key = line
            .key
            .as_deref()
            .ok_or_else(|| PyValueError::new_err("line is not an assignment"))?;
        Ok(line.quoted || key_looks_secret(key))
    }

    /// Re-emit `lines` as .env.example text with values rewritten per `mode`.
    #[pyfunction]
    fn render_example(lines: Vec<PyRef<'_, Line>>, mode: &str) -> PyResult<String> {
        let mode = Mode::parse(mode)?;
        let refs: Vec<&Line> = lines.iter().map(|l| &**l).collect();
        Ok(render(&refs, mode))
    }

    /// Parse `text` and render the example in one step (no Python Line objects).
    #[pyfunction]
    fn generate_example(text: &str, mode: &str) -> PyResult<String> {
        let mode = Mode::parse(mode)?;
        let lines: Vec<Line> = splitlines(text).into_iter().map(parse_line).collect();
        let refs: Vec<&Line> = lines.iter().collect();
        Ok(render(&refs, mode))
    }
}
