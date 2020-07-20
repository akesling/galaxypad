use std::cell::RefCell;
use std::collections::HashMap;
use std::error::Error;
use std::fmt::Debug;
use std::ptr;
use std::rc::Rc;

// See video course https://icfpcontest2020.github.io/#/post/2054

struct Constants {
    cons: ExprRef,
    t: ExprRef,
    f: ExprRef,
    nil: ExprRef,
}

type ExprRef = Rc<RefCell<dyn Expr>>;
trait Expr: Debug {
    fn name(&self) -> Option<&str>;
    fn func(&self) -> Option<ExprRef>;
    fn arg(&self) -> Option<ExprRef>;
    fn evaluated(&self) -> Option<ExprRef>;
    // NOTE(akesling): Beware memory leaks through circular dependencies on evaluated results!
    fn set_evaluated(&mut self, ExprRef) -> Result<(), String>;
}

#[derive(Default, Debug, Clone)]
struct Atom {
    name: String,
}

fn Atom(name: String) -> Rc<RefCell<dyn Expr>> {
    return Rc::new(RefCell::new(Atom { name }));
}

impl Expr for Atom {
    fn name(&self) -> Option<&str> {
        Some(&self.name)
    }

    fn func(&self) -> Option<ExprRef> {
        None
    }

    fn arg(&self) -> Option<ExprRef> {
        None
    }

    fn evaluated(&self) -> Option<ExprRef> {
        None
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        Err(format!(
            "Attempted to set Atom to evaluated with value: {:?}",
            expr
        ))
    }
}

impl Expr for &Atom {
    fn name(&self) -> Option<&str> {
        Some(&self.name)
    }

    fn func(&self) -> Option<ExprRef> {
        None
    }

    fn arg(&self) -> Option<ExprRef> {
        None
    }

    fn evaluated(&self) -> Option<ExprRef> {
        None
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        Err(format!(
            "Attempted to set Atom to evaluated with value: {:?}",
            expr
        ))
    }
}

#[derive(Debug, Clone)]
struct Ap {
    _evaluated: Option<ExprRef>,

    func: ExprRef,
    arg: ExprRef,
}

fn Ap(func: ExprRef, arg: ExprRef) -> Rc<RefCell<dyn Expr>> {
    return Rc::new(RefCell::new(Ap {
        func,
        arg,
        _evaluated: None,
    }));
}

impl Expr for Ap {
    fn name(&self) -> Option<&str> {
        None
    }

    fn func(&self) -> Option<ExprRef> {
        Some(self.func.clone())
    }

    fn arg(&self) -> Option<ExprRef> {
        Some(self.arg.clone())
    }

    fn evaluated(&self) -> Option<ExprRef> {
        return self._evaluated.clone();
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        self._evaluated = Some(expr.clone());
        Ok(())
    }
}

impl Expr for &Ap {
    fn name(&self) -> Option<&str> {
        None
    }

    fn func(&self) -> Option<ExprRef> {
        Some(self.func.clone())
    }

    fn arg(&self) -> Option<ExprRef> {
        Some(self.arg.clone())
    }

    fn evaluated(&self) -> Option<ExprRef> {
        return self._evaluated.clone();
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        let mut evaluated = &self._evaluated;
        evaluated = &Some(expr.clone());
        Ok(())
    }
}

#[derive(Default)]
struct Point {
    x: u64,
    y: u64,
}

fn parse_functions(script_string: &str) -> HashMap<String, ExprRef> {
    panic!("Parse functions is not yet implemented");
}

fn interact(
    state: ExprRef,
    event: ExprRef,
    functions: &HashMap<String, ExprRef>,
    constants: &Constants,
) -> (ExprRef, ExprRef) {
    // See https://message-from-space.readthedocs.io/en/latest/message38.html
    let expr: ExprRef = Ap(Ap(Atom("galaxy".to_owned()), state.clone()), event.clone());
    let res: ExprRef = eval(expr, functions, constants).unwrap();
    // Note: res will be modulatable here (consists of cons, nil and numbers only)
    let items = get_list_items_from_expr(res).unwrap();
    if items.len() < 3 {
        panic!(
            "List was of unexpected length {}, expected 3 items",
            items.len()
        );
    }
    let (flag, newState, data) = (items[0].clone(), items[1].clone(), items[2].clone());
    if (as_num(flag).unwrap() == 0) {
        return (newState, data);
    }
    return interact(newState, send_to_alien_proxy(data), functions, constants);
}

fn send_to_alien_proxy(expr: ExprRef) -> ExprRef {
    panic!("send_to_alien_proxy is not yet implemented");
}

fn as_num(expr: ExprRef) -> Result<i64, String> {
    if let Some(name) = expr.borrow().name().as_ref() {
        return Ok(parse_number(name)?);
    }
    Err(format!("Not a number: {:?}", expr))
}

fn parse_number(name: &str) -> Result<i64, String> {
    if let Ok(i) = name.parse::<i64>() {
        return Ok(i);
    }

    if (name == "t") {
        return Ok(1);
    }

    if (name == "f") {
        return Ok(0);
    }

    return Err(format!("Failed to parse {} as a number", name))
}

fn get_list_items_from_expr(expr: ExprRef) -> Result<Vec<ExprRef>, String> {
    if let Some(name) = expr.borrow().name().as_ref() {
        if name == &"nil" {
            return Ok(vec![expr.clone()]);
        } else {
            return Err(format!("First item in list was non-nil Atom({}) not Ap", name))
        }
    } else {
        let second = expr.borrow().func().unwrap().clone();
        if let Some(name) = second.borrow().name().as_ref() {
            return Err(format!("Second item in list was non-nil Atom({}) not Ap", name))
        }

        let cons = expr.borrow().func().unwrap().clone();
        if let Some(name) = second.borrow().name().as_ref() {
            if name != &"cons" {
                return Err(format!("Cons-place item in list was Atom({}) not cons", name))
            }
        }

        let mut flattened = vec![second.borrow().arg().unwrap()];

        let next = expr.borrow().arg().unwrap();
        if let Some(name) = second.clone().borrow().name().as_ref() {
            return Ok(flattened);
        } else {
            flattened.extend(get_list_items_from_expr(next)?);
            return Ok(flattened);
        }
    }
}

fn eval(
    expr: ExprRef,
    functions: &HashMap<String, ExprRef>,
    constants: &Constants,
) -> Result<ExprRef, String> {
    match expr.borrow().evaluated() {
        Some(expr) => {
            return Ok(expr);
        }
        None => {
            let mut current_expr = expr.clone();
            loop {
                let result = try_eval(current_expr.clone(), functions, constants)?;
                if ptr::eq(current_expr.as_ref(), result.as_ref()) {
                    // XXX: Circular reference -- memory leak
                    current_expr.borrow_mut().set_evaluated(result.clone())?;
                    return Ok(result);
                } else {
                    current_expr = result.clone();
                }
            }
        }
    }
}

fn try_eval(
    expr: ExprRef,
    functions: &HashMap<String, ExprRef>,
    constants: &Constants,
) -> Result<ExprRef, String> {
    match expr.borrow().evaluated() {
        Some(x) => {
            return Ok(x.clone());
        }
        None => {
            if let Some(name) = expr.borrow().name().as_ref() {
                if let Some(function) = functions.get(name.to_owned()) {
                    return Ok(function.clone());
                }
            } else {
                let func = eval(expr.clone(), functions, constants)?;
                let x = expr.borrow().arg().unwrap().clone();
                if let Some(name) = expr.borrow().name().as_ref() {
                    match *name {
                        "neg" => {
                            return Ok(Atom(
                                (-as_num(eval(x, functions, constants)?)?).to_string(),
                            ));
                        }
                        "i" => {
                            return Ok(x);
                        }
                        "nil" => {
                            return Ok(constants.t.clone());
                        }
                        "isnil" => {
                            return Ok(Ap(
                                x,
                                Ap(
                                    constants.t.clone(),
                                    Ap(constants.t.clone(), constants.f.clone()),
                                ),
                            ));
                        }
                        "car" => {
                            return Ok(Ap(x, constants.t.clone()));
                        }
                        "car" => {
                            return Ok(Ap(x, constants.f.clone()));
                        }
                        _ => (),
                    }
                } else {
                    let func2 = eval(func.clone(), functions, constants)?.clone();
                    let y = func.borrow().arg().unwrap().clone();
                    if let Some(name) = func2.clone().borrow().name().as_ref() {
                        match *name {
                            "t" => {
                                return Ok(y);
                            }
                            "f" => {
                                return Ok(x);
                            }
                            "add" => {
                                return Ok(Atom(
                                    (as_num(eval(x, functions, constants)?)?
                                        + as_num(eval(y, functions, constants)?)?)
                                    .to_string(),
                                ));
                            }
                            "mul" => {
                                return Ok(Atom(
                                    (as_num(eval(x, functions, constants)?)?
                                        * as_num(eval(y, functions, constants)?)?)
                                    .to_string(),
                                ));
                            }
                            "div" => {
                                return Ok(Atom(
                                    (as_num(eval(x, functions, constants)?)?
                                        / as_num(eval(y, functions, constants)?)?)
                                    .to_string(),
                                ));
                            }
                            "eq" => {
                                let are_equal = as_num(eval(x, functions, constants)?)?
                                    == as_num(eval(y, functions, constants)?)?;
                                return Ok(if are_equal {
                                    constants.t.clone()
                                } else {
                                    constants.f.clone()
                                });
                            }
                            "lt" => {
                                let is_less_than = as_num(eval(x, functions, constants)?)?
                                    < as_num(eval(y, functions, constants)?)?;
                                return Ok(if is_less_than {
                                    constants.t.clone()
                                } else {
                                    constants.f.clone()
                                });
                            }
                            "cons" => {
                                return Ok(eval_cons(y, x, functions, constants)?);
                            }
                            _ => (),
                        }
                    } else {
                        let func3 =
                            eval(func2.borrow().func().unwrap(), functions, constants)?.clone();
                        let z = func3.borrow().arg().unwrap();
                        if let Some(name) = func3.clone().borrow().name().as_ref() {
                            match *name {
                                "s" => return Ok(Ap(Ap(z, x.clone()), Ap(y, x))),
                                "c" => return Ok(Ap(Ap(z, x), y)),
                                "b" => return Ok(Ap(z, Ap(y, x))),
                                "cons" => return Ok(Ap(Ap(x, z), y)),
                                _ => (),
                            }
                        }
                    }
                }
            }
        }
    }

    Ok(expr.clone())
}

fn eval_cons(
    head: ExprRef,
    tail: ExprRef,
    functions: &HashMap<String, ExprRef>,
    constants: &Constants,
) -> Result<ExprRef, String> {
    let res = Ap(
        Ap(constants.cons.clone(), eval(head, functions, constants)?),
        eval(tail, functions, constants)?,
    );
    // XXX: Circular reference -- memory leak
    res.borrow_mut().set_evaluated(res.clone());
    return Ok(res);
}

fn print_images(points: ExprRef) {
    panic!("print_images is not yet implemented");
}

fn request_click_from_user() -> Point {
    panic!("request_click_from_user is not yet implemented");
}

fn main() {
    let functions = parse_functions("DUMMY VALUE");
    let constants = Constants {
        cons: Atom("cons".to_owned()),
        t: Atom("t".to_owned()),
        f: Atom("f".to_owned()),
        nil: Atom("nil".to_owned()),
    };

    // See https://message-from-space.readthedocs.io/en/latest/message39.html
    let mut state: ExprRef = constants.nil.clone();
    let mut point = Point { x: 0, y: 0 };

    loop {
        let click = Ap(
            Ap(constants.cons.clone(), Atom(point.x.to_string())),
            Atom(point.y.to_string()),
        );
        let (newState, images) = interact(state.clone(), click.clone(), &functions, &constants);
        print_images(images);
        point = request_click_from_user();
        state = newState;
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn pseudo_it_works() {
        assert_eq!(2 + 2, 4);
    }
}
