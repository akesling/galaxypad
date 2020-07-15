use std::mem;
use std::process;

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

use icfpjit::jit;

/// SimpleJIT Test
#[pyfunction]
fn hello_jit() -> PyResult<String> {
    // Create the JIT instance, which manages all generated functions and data.
    let mut jit = jit::JIT::new();

    // A small test function.
    //
    // The `(c)` declares a return variable; the function returns whatever value
    // it was assigned when the function exits. Note that there are multiple
    // assignments, so the input is not in SSA form, but that's ok because
    // Cranelift handles all the details of translating into SSA form itself.
    let foo_code = r#"
        fn foo(a, b) -> (c) {
            c = if a {
                if b {
                    30
                } else {
                    40
                }
            } else {
                50
            }
            c = c + 2
        }
    "#;

    // Pass the string to the JIT, and it returns a raw pointer to machine code.
    let foo = jit.compile(&foo_code).unwrap_or_else(|msg| {
        eprintln!("error: {}", msg);
        process::exit(1);
    });

    // Cast the raw pointer to a typed function pointer. This is unsafe, because
    // this is the critical point where you have to trust that the generated code
    // is safe to be called.
    //
    // TODO: Is there a way to fold this transmute into `compile` above?
    let foo = unsafe { mem::transmute::<_, fn(isize, isize) -> isize>(foo) };

    // And now we can call it!
    Ok(format!("the answer is: {}", foo(1, 0)))
}

/// A simple function to try all this out
#[pyfunction]
fn hello_python() -> PyResult<String> {
    Ok("Hello Python!".to_owned())
}

/// A Python module implemented in Rust.
#[pymodule]
fn sidecar(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(hello_python))?;
    m.add_wrapped(wrap_pyfunction!(hello_jit))?;

    Ok(())
}
