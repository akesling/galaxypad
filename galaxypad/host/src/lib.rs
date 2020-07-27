mod utils;

use wasm_bindgen::prelude::*;
use runtime::{entry_point, Point};

// When the `wee_alloc` feature is enabled, use `wee_alloc` as the global
// allocator.
#[cfg(feature = "wee_alloc")]
#[global_allocator]
static ALLOC: wee_alloc::WeeAlloc = wee_alloc::WeeAlloc::INIT;

#[wasm_bindgen]
extern {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);

    fn render_image(image: Box<[i64]>);
}

#[wasm_bindgen]
pub fn greet() {
    log("Hello, host!");
}

fn print_images(points: Vec<Vec<(i64, i64)>>) {
    log(&format!("{:?}", points));
}

fn render_images(images: Vec<Vec<(i64, i64)>>, renderer: &js_sys::Function) {
    log(&format!("Rust rendering {:?}", images));
    for points in images.iter() {
        let this = JsValue::null();
        let ps_for_js: Vec<Vec<i64>> = points.iter().map(|p| vec![p.0, p.1]).collect();
        let x = JsValue::from_serde(&points).unwrap();
        let _ = renderer.call1(&this, &x);
    }
}

fn click_panic() -> Point {
    log("Click receipt is not yet implemented.");
    panic!("Click receipt is not yet implemented.");
}

pub fn recurse_stack(stack: &mut Vec<usize>, stack_depth: usize) {
    for i in 0..100_000_000 {
        stack.push(stack.len());
        if i % 10_000_000 == 0 {
            log(&format!("Stack size: {}", stack.len()));
        }
    }
    log(&format!("Recursing at {}, stack depth: {}", stack.len(), stack_depth));
    recurse_stack(stack, stack_depth + 1);
}

pub fn stack_fn_entry() {
    let mut stack: Vec<usize> = vec![];
    recurse_stack(&mut stack, 0);
}

#[wasm_bindgen]
pub fn test_stack_size() {
    stack_fn_entry();
}

#[wasm_bindgen]
pub fn start_galaxy_pad(renderer: &js_sys::Function) {
    let callback = entry_point(&click_panic, &|images| render_images(images, renderer), &log);
}
