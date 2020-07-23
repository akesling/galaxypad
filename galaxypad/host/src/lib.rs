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
}

#[wasm_bindgen]
pub fn greet() {
    log("Hello, host!");
}

fn print_names(points: Vec<Vec<(i64, i64)>>) {
    log(&format!("{:?}", points));
}

fn click_panic() -> Point {
    panic!("Click receipt is not yet implemented.");
}

#[wasm_bindgen]
pub fn test_stack_size(stack_depth: i32) {
    log(&format!("{}", stack_depth));
    test_stack_size(stack_depth + 1);
}

#[wasm_bindgen]
pub fn start_galaxy_pad() {
    let callback = entry_point(&click_panic, &print_names);
}
