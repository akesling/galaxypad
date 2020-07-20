#[macro_use]
extern crate maplit;
#[macro_use]
extern crate lazy_static;

use std::cell::RefCell;
use std::collections::{HashMap, HashSet};
use std::fmt::Debug;
use std::fs;
use std::ptr;
use std::rc::{Rc, Weak};

// See video course https://icfpcontest2020.github.io/#/post/2054

struct Constants {
    cons: ExprRef,
    t: ExprRef,
    f: ExprRef,
    nil: ExprRef,
}

lazy_static! {
    static ref ATOMS: HashSet<String> = hashset!{
        "add".to_owned(),
        //"inc",
        //"dec",
        "i".to_owned(),
        "t".to_owned(),
        "f".to_owned(),
        "mul".to_owned(),
        "div".to_owned(),
        "eq".to_owned(),
        "lt".to_owned(),
        "neg".to_owned(),
        "s".to_owned(),
        "c".to_owned(),
        "b".to_owned(),
        //"pwr2",
        "cons".to_owned(),
        "car".to_owned(),
        "cdr".to_owned(),
        "nil".to_owned(),
        "isnil".to_owned(),
        //"vec",
        //"if0",
        //"send",
        //"checkerboard",
        //"draw",
        //"multipledraw",
        //"modem",
        //"f38",
        //"statelessdraw",
        //"interact",
    };
}

type ExprRef = Rc<RefCell<dyn Expr>>;
type WeakExprRef = Weak<RefCell<dyn Expr>>;
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
    _evaluated: Option<WeakExprRef>,
}

fn atom(name: String) -> Rc<RefCell<dyn Expr>> {
    return Rc::new(RefCell::new(Atom { name, _evaluated: None }));
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
        return match &self._evaluated {
            Some(weak) => Some(weak.upgrade().unwrap()),
            None => None,
        }
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        self._evaluated = Some(Rc::downgrade(&expr));
        Ok(())
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
        return match &self._evaluated {
            Some(weak) => Some(weak.upgrade().unwrap()),
            None => None,
        }
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        (*self).set_evaluated(expr)
    }

}

#[derive(Debug, Clone)]
struct Ap {
    _evaluated: Option<WeakExprRef>,

    func: ExprRef,
    arg: ExprRef,
}

fn ap(func: ExprRef, arg: ExprRef) -> Rc<RefCell<dyn Expr>> {
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
        return match &self._evaluated {
            Some(weak) => Some(weak.upgrade().unwrap()),
            None => None,
        }
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        self._evaluated = Some(Rc::downgrade(&expr));
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
        return match &self._evaluated {
            Some(weak) => Some(weak.upgrade().unwrap()),
            None => None,
        }
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        (*self).set_evaluated(expr)
    }
}

#[derive(Default)]
struct Point {
    x: u64,
    y: u64,
}

// Takes a vector of tokens and recursively consumes the tail of the token vector
fn deserialize(tokens: Vec<&str>) -> Result<(ExprRef, Vec<&str>), String> {
    let candidate_token = tokens[0];
    if candidate_token == "ap" {
        let (left, left_remainder) = deserialize(tokens[1..].to_vec())?;
        let (right, right_remainder) = deserialize(left_remainder)?;
        let ap_expr = ap(left, right);
        return Ok((ap_expr, right_remainder));
    }

    if ATOMS.contains(candidate_token) {
        return Ok((atom(candidate_token.to_owned()), tokens[1..].to_vec()));
    }

    if let Ok(i) = candidate_token.parse::<i64>() {
        return Ok((atom(i.to_string()), tokens[1..].to_vec()));
    }

    if candidate_token.starts_with(':') {
        return Ok((atom(candidate_token.to_owned()), tokens[1..].to_vec()));
    }

    return Err(format!(
        "Could not deserialize \"{}\" with remainder {:?}",
        candidate_token,
        tokens[1..].to_vec()
    ));
}

// Loads a function definition, which must be of the form:
// <name> = <body expr>
fn load_function(line: &str) -> Result<(String, ExprRef), String> {
    let left_and_right: Vec<&str> = line.split('=').filter(|s| !s.is_empty()).collect();
    assert!(
        left_and_right.len() == 2,
        "Function line could not be split in two"
    );

    let left_tokens: Vec<&str> = left_and_right[0]
        .split(' ')
        .filter(|s| !s.is_empty())
        .collect();
    assert!(
        left_tokens.len() == 1,
        format!("Function name was longer than expected {:?}", left_tokens)
    );
    let function_name = left_tokens[0].to_owned();

    let right_tokens: Vec<&str> = left_and_right[1]
        .split(' ')
        .filter(|s| !s.is_empty())
        .collect();
    assert!(right_tokens.len() > 0, "Function body was of length zero");
    let (function_body, remainder) = deserialize(right_tokens)?;
    assert!(
        remainder.len() == 0,
        format!(
            "Function body did not cleanly parse, tokens remained: {:?}",
            remainder
        )
    );

    Ok((function_name, function_body))
}

// Opens the given filename and attempts to load each line as a function
// definition (pretty much just for galaxy.txt)
fn load_function_definitions(file_path: &str) -> Result<HashMap<String, ExprRef>, String> {
    return fs::read_to_string(file_path)
        .expect(&format!(
            "Something went wrong reading the functions file {}",
            file_path
        ))
        .split('\n')
        .filter(|s| !s.is_empty())
        .map(|line| load_function(line))
        .collect();
}

fn interact(
    state: ExprRef,
    event: ExprRef,
    functions: &HashMap<String, ExprRef>,
    constants: &Constants,
) -> (ExprRef, ExprRef) {
    // See https://message-from-space.readthedocs.io/en/latest/message38.html
    let expr: ExprRef = ap(ap(atom("galaxy".to_owned()), state.clone()), event.clone());
    println!("Eval'ing");
    let res: ExprRef = eval(expr, functions, constants, 0).unwrap();
    // Note: res will be modulatable here (consists of cons, nil and numbers only)
    println!("Converting results to a list");
    let items = get_list_items_from_expr(res).unwrap();
    if items.len() < 3 {
        panic!(
            "List was of unexpected length {}, expected 3 items",
            items.len()
        );
    }
    let (flag, new_state, data) = (items[0].clone(), items[1].clone(), items[2].clone());
    if as_num(flag).unwrap() == 0 {
        return (new_state, data);
    }
    println!("Recursing through interact");
    return interact(new_state, send_to_alien_proxy(data), functions, constants);
}

fn send_to_alien_proxy(_expr: ExprRef) -> ExprRef {
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

    if name == "t" {
        return Ok(1);
    }

    if name == "f" {
        return Ok(0);
    }

    return Err(format!("Failed to parse {} as a number", name));
}

fn get_list_items_from_expr(expr: ExprRef) -> Result<Vec<ExprRef>, String> {
    if let Some(name) = expr.borrow().name().as_ref() {
        if name == &"nil" {
            return Ok(vec![expr.clone()]);
        } else {
            return Err(format!(
                "First item in list was non-nil atom({}) not Ap",
                name
            ));
        }
    } else {
        let second = expr.borrow().func().unwrap().clone();
        if let Some(name) = second.borrow().name().as_ref() {
            return Err(format!(
                "Second item in list was non-nil atom({}) not Ap",
                name
            ));
        }

        let cons = second.borrow().func().unwrap().clone();
        if let Some(name) = cons.borrow().name().as_ref() {
            if name != &"cons" {
                return Err(format!(
                    "Cons-place item in list was atom({}) not cons",
                    name
                ));
            }
        }

        let mut flattened = vec![second.borrow().arg().unwrap()];

        let next = expr.borrow().arg().unwrap();
        if let Some(name) = next.clone().borrow().name().as_ref() {
            if name == &"nil" {
                return Ok(flattened);
            } else {
                return Err(format!(
                    "get_list_items_from_expr somehow got a non-nil end node in a list {}",
                    name
                ));
            }
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
    stack_depth: u64,
) -> Result<ExprRef, String> {
    println!("Eval stack depth {}", stack_depth);
    if let Some(x) = expr.borrow().evaluated() {
        return Ok(x);
    }

    let mut current_expr = expr.clone();
    loop {
        let result = try_eval(current_expr.clone(), functions, constants, stack_depth+1)?;
        println!("Result achieved through try_eval, attempted to see if its the same or not.");
        if !ptr::eq(current_expr.as_ref(), result.as_ref()) {
            current_expr = result.clone();
            continue;
        }
        println!("Looks like they're the same");

        if let Some(x) = current_expr.borrow().evaluated() {
            return Ok(x);
        }

        // XXX: Circular reference -- memory leak
        current_expr.borrow_mut().set_evaluated(result.clone())?;
        println!("Evaluated is now set");
        return Ok(result);
    }
}

fn try_eval(
    expr: ExprRef,
    functions: &HashMap<String, ExprRef>,
    constants: &Constants,
    stack_depth: u64,
) -> Result<ExprRef, String> {
    println!("TryEval stack depth {}", stack_depth);
    if let Some(x) = expr.borrow().evaluated() {
        println!("Already evaluated!");
        return Ok(x.clone());
    }
    println!("Not yet evaluated");

    if let Some(name) = expr.borrow().name().as_ref() {
        println!("It's an atom");
        if let Some(function) = functions.get(name.to_owned()) {
            println!("And a function");
            return Ok(function.clone());
        }
        println!("Not a function");
    } else {
        println!("Expr is ap");
        println!("Func evaling");
        let func = eval(expr.borrow().func().unwrap().clone(), functions, constants, stack_depth+1)?;
        println!("Func evaluated");
        let x = expr.borrow().arg().unwrap().clone();
        if let Some(name) = func.clone().borrow().name().as_ref() {
            println!("Func is atom");
            match *name {
                "neg" => {
                    return Ok(atom(
                        (-as_num(eval(x, functions, constants, stack_depth+1)?)?).to_string(),
                    ));
                }
                "i" => {
                    return Ok(x);
                }
                "nil" => {
                    return Ok(constants.t.clone());
                }
                "isnil" => {
                    return Ok(ap(
                        x,
                        ap(
                            constants.t.clone(),
                            ap(constants.t.clone(), constants.f.clone()),
                        ),
                    ));
                }
                "car" => {
                    return Ok(ap(x, constants.t.clone()));
                }
                "cdr" => {
                    return Ok(ap(x, constants.f.clone()));
                }
                _ => (),
            }
        } else {
            println!("Expr.func is ap");
            let tmp_func2 = func.borrow().func().unwrap().clone();
            let func2 = eval(tmp_func2, functions, constants, stack_depth+1)?.clone();
            println!("Expr.func.func2 evaled");
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
                        return Ok(atom(
                            (as_num(eval(x, functions, constants, stack_depth+1)?)?
                                + as_num(eval(y, functions, constants, stack_depth+1)?)?)
                            .to_string(),
                        ));
                    }
                    "mul" => {
                        return Ok(atom(
                            (as_num(eval(x, functions, constants, stack_depth+1)?)?
                                * as_num(eval(y, functions, constants, stack_depth+1)?)?)
                            .to_string(),
                        ));
                    }
                    "div" => {
                        return Ok(atom(
                            (as_num(eval(x, functions, constants, stack_depth+1)?)?
                                / as_num(eval(y, functions, constants, stack_depth+1)?)?)
                            .to_string(),
                        ));
                    }
                    "eq" => {
                        let are_equal = as_num(eval(x, functions, constants, stack_depth+1)?)?
                            == as_num(eval(y, functions, constants, stack_depth+1)?)?;
                        return Ok(if are_equal {
                            constants.t.clone()
                        } else {
                            constants.f.clone()
                        });
                    }
                    "lt" => {
                        let is_less_than = as_num(eval(x, functions, constants, stack_depth+1)?)?
                            < as_num(eval(y, functions, constants, stack_depth+1)?)?;
                        return Ok(if is_less_than {
                            constants.t.clone()
                        } else {
                            constants.f.clone()
                        });
                    }
                    "cons" => {
                        return Ok(eval_cons(y, x, functions, constants, stack_depth+1)?);
                    }
                    _ => (),
                }
            } else {
                let func3 =
                    eval(func2.borrow().func().unwrap(), functions, constants, stack_depth+1)?.clone();
                let z = func2.borrow().arg().unwrap();
                if let Some(name) = func3.clone().borrow().name().as_ref() {
                    match *name {
                        "s" => return Ok(ap(ap(z, x.clone()), ap(y, x))),
                        "c" => return Ok(ap(ap(z, x), y)),
                        "b" => return Ok(ap(z, ap(y, x))),
                        "cons" => return Ok(ap(ap(x, z), y)),
                        _ => (),
                    }
                }
            }
        }
    }
    println!("Nothing matched");

    let result = expr.clone();
    println!("Returning.");
    return Ok(result)

//    Ok(expr.clone())
}

fn eval_cons(
    head: ExprRef,
    tail: ExprRef,
    functions: &HashMap<String, ExprRef>,
    constants: &Constants,
    stack_depth: u64,
) -> Result<ExprRef, String> {
    println!("EvalCons stack depth {}", stack_depth);
    let res = ap(
        ap(constants.cons.clone(), eval(head, functions, constants, stack_depth+1)?),
        eval(tail, functions, constants, stack_depth+1)?,
    );
    // XXX: Circular reference -- memory leak
    res.borrow_mut().set_evaluated(res.clone())?;
    return Ok(res);
}

fn print_images(_points: ExprRef) {
    panic!("print_images is not yet implemented");
}

fn request_click_from_user() -> Point {
    panic!("request_click_from_user is not yet implemented");
}

fn main() {
    println!("Start main");
    println!("Parsing functions");
    let functions: HashMap<String, ExprRef> = load_function_definitions("galaxy.txt").unwrap();
    println!("Setting up constants");
    let constants = Constants {
        cons: atom("cons".to_owned()),
        t: atom("t".to_owned()),
        f: atom("f".to_owned()),
        nil: atom("nil".to_owned()),
    };

    // See https://message-from-space.readthedocs.io/en/latest/message39.html
    let mut state: ExprRef = constants.nil.clone();
    let mut point = Point { x: 0, y: 0 };

    println!("Starting loop");
    loop {
        let click = ap(
            ap(constants.cons.clone(), atom(point.x.to_string())),
            atom(point.y.to_string()),
        );
        println!("Staring 'interact' protocol");
        let (new_state, images) = interact(state.clone(), click.clone(), &functions, &constants);
        print_images(images);
        point = request_click_from_user();
        state = new_state;
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn pseudo_it_works() {
        assert_eq!(2 + 2, 4);
    }
}
