# Research Output – 2026-01-12 20:33 CET

## Original Prompt
> Research best rust patterns. Use the research file to create a .kiro/steering/rust_patterns.md file

## Complete Response

# Rust Patterns Research

## Core Rust Patterns

### 1. Ownership and Memory Safety Patterns

**Ownership Transfer Pattern**
```rust
fn take_ownership(data: String) -> String {
    // Function takes ownership of data
    data.to_uppercase()
}
```

**Borrowing Pattern**
```rust
fn analyze_text(text: &str) -> usize {
    text.split_whitespace().count()
}

fn process_data(data: &mut Vec<i32>) {
    data.sort();
    data.dedup();
}
```

**RAII (Resource Acquisition Is Initialization) Pattern**
- Automatic cleanup through Drop trait
- Tie resource lifetime to scope
- Prevents resource leaks through compile-time guarantees

### 2. Error Handling Patterns

**Result and Option Types**
```rust
fn safe_divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        Err("Division by zero".to_string())
    } else {
        Ok(a / b)
    }
}

fn parse_number(input: &str) -> Option<i32> {
    input.trim().parse().ok()
}
```

**Error Propagation with ?**
```rust
fn process_config_file(path: &str) -> Result<Config, Box<dyn std::error::Error>> {
    let content = fs::read_to_string(path)?;
    let config: Config = serde_json::from_str(&content)?;
    validate_config(&config)?;
    Ok(config)
}
```

**Pattern Matching for Error Handling**
- Use match statements for explicit error handling
- Exhaustive matching ensures all cases are covered
- Combines safety with expressiveness

### 3. Trait Patterns

**Trait Definition and Implementation**
```rust
trait Drawable {
    fn draw(&self);
    fn area(&self) -> f64;
    
    // Default implementation
    fn describe(&self) {
        println!("This shape has area: {}", self.area());
    }
}
```

**Generic Traits with Associated Types**
```rust
trait Iterator {
    type Item;
    
    fn next(&mut self) -> Option<Self::Item>;
    
    fn collect<B: FromIterator<Self::Item>>(self) -> B
    where
        Self: Sized,
    {
        FromIterator::from_iter(self)
    }
}
```

**Trait Objects for Dynamic Dispatch**
```rust
trait EventHandler {
    fn handle(&self, event: &Event);
}

struct EventProcessor {
    handlers: Vec<Box<dyn EventHandler>>,
}
```

### 4. Smart Pointer Patterns

**Reference Counting (Rc/Arc)**
```rust
use std::rc::Rc;
use std::sync::Arc;

// Single-threaded reference counting
let data = Rc::new(vec![1, 2, 3, 4, 5]);
let data_clone = Rc::clone(&data);

// Thread-safe reference counting
let shared_data = Arc::new(vec![1, 2, 3, 4, 5]);
let shared_clone = Arc::clone(&shared_data);
```

**Interior Mutability (RefCell/Mutex)**
```rust
use std::cell::RefCell;
use std::sync::Mutex;

// Single-threaded interior mutability
let data = RefCell::new(vec![1, 2, 3]);
data.borrow_mut().push(4);

// Thread-safe interior mutability
let data = Mutex::new(vec![1, 2, 3]);
data.lock().unwrap().push(4);
```

### 5. Concurrency Patterns

**Async/Await Fundamentals**
```rust
use tokio::time::{sleep, Duration};

async fn fetch_data(url: &str) -> Result<String, reqwest::Error> {
    let response = reqwest::get(url).await?;
    let content = response.text().await?;
    Ok(content)
}

async fn process_multiple_urls(urls: Vec<&str>) -> Vec<Result<String, reqwest::Error>> {
    let futures: Vec<_> = urls.into_iter()
        .map(|url| fetch_data(url))
        .collect();
    
    futures::future::join_all(futures).await
}
```

**Channel Communication**
```rust
use tokio::sync::mpsc;

#[derive(Debug)]
enum Message {
    Text(String),
    Quit,
}

async fn message_processor() {
    let (tx, mut rx) = mpsc::channel(100);
    
    tokio::spawn(async move {
        tx.send(Message::Text("Hello".to_string())).await.unwrap();
        tx.send(Message::Quit).await.unwrap();
    });
    
    while let Some(msg) = rx.recv().await {
        match msg {
            Message::Text(text) => println!("Received: {}", text),
            Message::Quit => break,
        }
    }
}
```

**Shared State with Arc and Mutex**
```rust
use std::sync::{Arc, Mutex};
use tokio::task;

#[derive(Clone)]
struct Counter {
    value: Arc<Mutex<i32>>,
}

impl Counter {
    fn new() -> Self {
        Self {
            value: Arc::new(Mutex::new(0)),
        }
    }
    
    fn increment(&self) {
        let mut value = self.value.lock().unwrap();
        *value += 1;
    }
}
```

### 6. Builder Pattern

**Configuration Builder**
```rust
#[derive(Debug, Default)]
struct DatabaseConfig {
    host: String,
    port: u16,
    username: String,
    password: String,
    database: String,
}

struct DatabaseConfigBuilder {
    config: DatabaseConfig,
}

impl DatabaseConfigBuilder {
    fn new() -> Self {
        Self {
            config: DatabaseConfig::default(),
        }
    }
    
    fn host(mut self, host: impl Into<String>) -> Self {
        self.config.host = host.into();
        self
    }
    
    fn port(mut self, port: u16) -> Self {
        self.config.port = port;
        self
    }
    
    fn build(self) -> Result<DatabaseConfig, String> {
        if self.config.host.is_empty() {
            return Err("Host is required".to_string());
        }
        Ok(self.config)
    }
}
```

### 7. Iterator Patterns

**Custom Iterators**
```rust
struct Counter {
    current: usize,
    max: usize,
}

impl Counter {
    fn new(max: usize) -> Self {
        Self { current: 0, max }
    }
}

impl Iterator for Counter {
    type Item = usize;
    
    fn next(&mut self) -> Option<Self::Item> {
        if self.current < self.max {
            let current = self.current;
            self.current += 1;
            Some(current)
        } else {
            None
        }
    }
}
```

**Iterator Combinators**
```rust
fn process_data(numbers: Vec<i32>) -> Vec<String> {
    numbers
        .into_iter()
        .filter(|&x| x > 0)
        .map(|x| x * 2)
        .filter(|&x| x < 100)
        .map(|x| format!("Value: {}", x))
        .collect()
}
```

### 8. Pattern Matching

**Enum Pattern Matching**
```rust
#[derive(Debug)]
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(i32, i32, i32),
}

fn process_message(msg: Message) {
    match msg {
        Message::Quit => println!("Quit message received"),
        Message::Move { x, y } => println!("Move to ({}, {})", x, y),
        Message::Write(text) => println!("Text: {}", text),
        Message::ChangeColor(r, g, b) => println!("RGB({}, {}, {})", r, g, b),
    }
}
```

**Advanced Pattern Matching**
```rust
fn analyze_data(data: &[i32]) -> String {
    match data {
        [] => "Empty slice".to_string(),
        [single] => format!("Single element: {}", single),
        [first, second] => format!("Two elements: {}, {}", first, second),
        [first, .., last] => format!("Multiple elements, first: {}, last: {}", first, last),
    }
}
```

## Key Findings

- **Memory Safety**: Rust's ownership system prevents common memory bugs at compile time without garbage collection overhead
- **Zero-Cost Abstractions**: High-level constructs compile to efficient machine code with no runtime penalty
- **Fearless Concurrency**: Ownership and type system enable safe concurrent programming by preventing data races
- **Explicit Error Handling**: Result and Option types force explicit error handling, eliminating silent failures
- **Pattern Matching**: Exhaustive pattern matching ensures all cases are handled, improving code reliability
- **Trait System**: Flexible trait system enables code reuse and abstraction without runtime cost
- **RAII**: Automatic resource management through scope-based cleanup prevents resource leaks

## Sources & References

- [Rust Concurrency Patterns for Parallel Programming](https://earthly.dev/blog/rust-concurrency-patterns-parallel-programming/) — Comprehensive guide to concurrent programming patterns
- [Mastering Concurrency in Rust: Advanced Patterns with Async/Await and Tokio](https://omid.dev/2024/06/15/mastering-concurrency-in-rust/) — Advanced async programming patterns
- [Smart Pointers in Rust: A Comprehensive Guide](https://gencmurat.com/en/posts/smart-pointers-in-rust/) — Memory management with smart pointers
- [Error-Free Code: How Rust Simplifies Exception Handling](https://www.somethingsblog.com/2024/10/19/error-free-code-how-rust-simplifies-exception-handling/) — Pattern matching for error handling
- [Enums and Pattern Matching in Rust](https://serokell.io/blog/enums-and-pattern-matching) — Comprehensive enum and pattern matching guide

## Tools & Methods Used

- web_search: "Rust programming patterns 2024 2025 ownership borrowing traits async concurrency"
- web_search: "Rust design patterns 2024 builder pattern RAII iterator trait objects error handling"
- web_search: "Rust memory management patterns RAII smart pointers Arc Rc RefCell 2024"
- web_search: "Rust async await patterns tokio futures 2024 concurrency parallelism"
- web_search: "Rust pattern matching enum Result Option 2024 error handling"
- web_fetch: Advanced concurrency patterns from omid.dev

## Metadata

- Generated: 2026-01-12T20:33:33+01:00
- Model: Claude 3.5 Sonnet
- Session ID: N/A
- Tool calls total: 6
- Approximate duration: ~3 minutes

## Limitations & Confidence Notes

- Data current as of January 2026 – Rust ecosystem evolves rapidly with new patterns emerging
- Focus on established patterns rather than experimental features
- Examples simplified for clarity – production code requires additional error handling
- Async patterns specifically target Tokio runtime – other runtimes may have different approaches
- Recommended next steps: Explore specific pattern implementations in real projects, study Rust API guidelines for idiomatic code
