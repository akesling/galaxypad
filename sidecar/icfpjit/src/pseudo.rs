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

const T: &str = "t";
const F: &str = "t";
const CONS: &str = "cons";
const NIL: &str = "nil";

lazy_static! {
    static ref ATOMS: HashSet<&'static str> = hashset!{
        "add",
        //"inc",
        //"dec",
        "i",
        "t",
        "f",
        "mul",
        "div",
        "eq",
        "lt",
        "neg",
        "s",
        "c",
        "b",
        //"pwr2",
        "cons",
        "car",
        "cdr",
        "nil",
        "isnil",
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
    fn name(&self) -> Option<&str> {
        None
    }
    fn func(&self) -> Option<ExprRef> {
        None
    }
    fn arg(&self) -> Option<ExprRef> {
        None
    }
    fn evaluated(&self) -> Option<ExprRef>;
    // NOTE(akesling): Beware memory leaks through circular dependencies on evaluated results!
    fn set_evaluated(&mut self, ExprRef) -> Result<(), String>;
    fn equals(&self, other: ExprRef) -> bool;
}

// Implement Expr for references whose value type implements Expr
impl<T> Expr for &T
where
    T: Expr,
{
    fn name(&self) -> Option<&str> {
        (*self).name()
    }

    fn func(&self) -> Option<ExprRef> {
        (*self).func()
    }

    fn arg(&self) -> Option<ExprRef> {
        (*self).arg()
    }

    fn evaluated(&self) -> Option<ExprRef> {
        (*self).evaluated()
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        (*self).set_evaluated(expr)
    }

    fn equals(&self, other: ExprRef) -> bool {
        (*self).equals(other)
    }
}

#[derive(Debug)]
struct Atom {
    _evaluated: Option<WeakExprRef>,

    name: String,
}

impl Atom {
    fn new<T: std::string::ToString>(name: T) -> ExprRef {
        Rc::new(RefCell::new(Atom {
            name: name.to_string(),
            _evaluated: None,
        }))
    }
}

impl Expr for Atom {
    fn name(&self) -> Option<&str> {
        Some(&self.name)
    }

    fn evaluated(&self) -> Option<ExprRef> {
        match &self._evaluated {
            Some(weak) => weak.upgrade(),
            None => None,
        }
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        self._evaluated = Some(Rc::downgrade(&expr));
        Ok(())
    }

    fn equals(&self, other: ExprRef) -> bool {
        match other.borrow().name() {
            Some(name) => self.name == name,
            None => false,
        }
    }
}

#[derive(Debug)]
struct Ap {
    _evaluated: Option<WeakExprRef>,

    func: ExprRef,
    arg: ExprRef,
}

impl Ap {
    fn new(func: ExprRef, arg: ExprRef) -> ExprRef {
        Rc::new(RefCell::new(Ap {
            func,
            arg,
            _evaluated: None,
        }))
    }
}

impl Expr for Ap {
    fn func(&self) -> Option<ExprRef> {
        Some(self.func.clone())
    }

    fn arg(&self) -> Option<ExprRef> {
        Some(self.arg.clone())
    }

    fn evaluated(&self) -> Option<ExprRef> {
        match &self._evaluated {
            Some(weak) => weak.upgrade(),
            None => None,
        }
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        self._evaluated = Some(Rc::downgrade(&expr));
        Ok(())
    }

    fn equals(&self, other: ExprRef) -> bool {
        match (other.borrow().func(), other.borrow().arg()) {
            (Some(func), Some(arg)) => {
                self.func.borrow().equals(func) && self.arg.borrow().equals(arg)
            }
            _ => false,
        }
    }
}

#[derive(Default)]
struct Point {
    x: u64,
    y: u64,
}

/// Takes a vector of tokens and recursively consumes the tail of the token vector
fn deserialize(tokens: Vec<&str>) -> Result<(ExprRef, Vec<&str>), String> {
    let candidate_token = tokens[0];
    if candidate_token == "ap" {
        let (left, left_remainder) = deserialize(tokens[1..].to_vec())?;
        let (right, right_remainder) = deserialize(left_remainder)?;
        let ap_expr = Ap::new(left, right);
        return Ok((ap_expr, right_remainder));
    }

    if ATOMS.contains(candidate_token) {
        return Ok((Atom::new(candidate_token), tokens[1..].to_vec()));
    }

    if let Ok(i) = candidate_token.parse::<i64>() {
        return Ok((Atom::new(i), tokens[1..].to_vec()));
    }

    if candidate_token.starts_with(':') {
        return Ok((Atom::new(candidate_token), tokens[1..].to_vec()));
    }

    Err(format!(
        "Could not deserialize \"{}\" with remainder {:?}",
        candidate_token,
        tokens[1..].to_vec()
    ))
}

/// Loads a function definition, which must be of the form:
/// <name> = <body expr>
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
    assert!(!right_tokens.is_empty(), "Function body was of length zero");
    let (function_body, remainder) = deserialize(right_tokens)?;
    assert!(
        remainder.is_empty(),
        format!(
            "Function body did not cleanly parse, tokens remained: {:?}",
            remainder
        )
    );

    Ok((function_name, function_body))
}

/// Opens the given filename and attempts to load each line as a function
/// definition (pretty much just for galaxy.txt)
fn load_function_definitions(file_path: &str) -> Result<HashMap<String, ExprRef>, String> {
    fs::read_to_string(file_path)
        .unwrap_or_else(|_| {
            panic!(
                "Something went wrong reading the functions file {}",
                file_path
            )
        })
        .split('\n')
        .filter(|s| !s.is_empty())
        .map(|line| load_function(line))
        .collect()
}

fn interact(
    state: ExprRef,
    event: ExprRef,
    functions: &HashMap<String, ExprRef>,
) -> (ExprRef, ExprRef) {
    // See https://message-from-space.readthedocs.io/en/latest/message38.html
    let expr: ExprRef = Ap::new(Ap::new(Atom::new("galaxy"), state), event);
    let res: ExprRef = eval(expr, functions).unwrap();
    // Note: res will be modulatable here (consists of cons, nil and numbers only)
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

    interact(new_state, send_to_alien_proxy(data), functions)
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

    Err(format!("Failed to parse {} as a number", name))
}

fn flatten_point(points_expr: ExprRef) -> Result<(i64, i64), String> {
    if let Some(name) = points_expr.borrow().name().as_ref() {
        if name == &NIL {
            println!("Nil list provided to flatten_point");

            Ok((0, 0))
        } else {
            panic!("First item in list was non-nil atom({}) not Ap", name);
        }
    } else {
        let second = points_expr
            .borrow()
            .func()
            .ok_or_else(|| "func expected on points_expr of flatten_point")?;
        if let Some(name) = second.borrow().name().as_ref() {
            panic!("Second item in list was non-nil atom({}) not Ap", name);
        }

        let cons = second
            .borrow()
            .func()
            .ok_or_else(|| "func expected on second of flatten_point")?;
        if let Some(name) = cons.borrow().name().as_ref() {
            if name != &CONS {
                panic!("Cons-place item in list was atom({}) not cons", name);
            }
        }

        Ok((
            as_num(
                points_expr
                    .borrow()
                    .arg()
                    .ok_or_else(|| "arg expected on points_expr of flatten_point")?,
            )?,
            as_num(
                second
                    .clone()
                    .borrow()
                    .arg()
                    .ok_or_else(|| "arg expected on second of flatten_point")?,
            )?,
        ))
    }
}

fn get_list_items_from_expr(expr: ExprRef) -> Result<Vec<ExprRef>, String> {
    if let Some(name) = expr.borrow().name().as_ref() {
        if name == &NIL {
            Ok(vec![expr.clone()])
        } else {
            Err(format!(
                "First item in list was non-nil atom({}) not Ap",
                name
            ))
        }
    } else {
        let second = expr
            .borrow()
            .func()
            .ok_or_else(|| "func expected on func of get_list_items_from_expr")?;
        if let Some(name) = second.borrow().name().as_ref() {
            return Err(format!(
                "Second item in list was non-nil atom({}) not Ap",
                name
            ));
        }

        let cons = second
            .borrow()
            .func()
            .ok_or_else(|| "func expected on second of get_list_items_from_expr")?;
        if let Some(name) = cons.borrow().name().as_ref() {
            if name != &CONS {
                return Err(format!(
                    "Cons-place item in list was atom({}) not cons",
                    name
                ));
            }
        }

        let mut flattened = vec![second
            .borrow()
            .arg()
            .ok_or_else(|| "arg expected on second of get_list_items_from_expr")?];

        let next = expr
            .borrow()
            .arg()
            .ok_or_else(|| "arg expected on expr of get_list_items_from_expr")?;
        if let Some(name) = next.clone().borrow().name().as_ref() {
            if name == &NIL {
                Ok(flattened)
            } else {
                Err(format!(
                    "get_list_items_from_expr somehow got a non-nil end node in a list {}",
                    name
                ))
            }
        } else {
            flattened.extend(get_list_items_from_expr(next)?);

            Ok(flattened)
        }
    }
}

fn eval(expr: ExprRef, functions: &HashMap<String, ExprRef>) -> Result<ExprRef, String> {
    if let Some(x) = expr.borrow().evaluated() {
        return Ok(x);
    }

    let initial_expr = expr.clone();
    let mut current_expr = expr;
    loop {
        let result = try_eval(current_expr.clone(), functions)?;
        if !ptr::eq(current_expr.as_ref(), result.as_ref()) {
            current_expr = result;
            continue;
        }

        initial_expr.borrow_mut().set_evaluated(result.clone())?;
        return Ok(result);
    }
}
fn try_eval(expr: ExprRef, functions: &HashMap<String, ExprRef>) -> Result<ExprRef, String> {
    if let Some(x) = expr.borrow().evaluated() {
        return Ok(x);
    }

    if let Some(name) = expr.borrow().name().as_ref() {
        if let Some(function) = functions.get(name.to_owned()) {
            return Ok(function.clone());
        }
    } else {
        let func = eval(
            expr.borrow()
                .func()
                .ok_or_else(|| "func expected on expr of try_eval")?,
            functions,
        )?;
        let x = expr
            .borrow()
            .arg()
            .ok_or_else(|| "arg expected on expr of try_eval")?;
        if let Some(name) = func.clone().borrow().name().as_ref() {
            match *name {
                "neg" => {
                    return Ok(Atom::new(-as_num(eval(x, functions)?)?));
                }
                "i" => {
                    return Ok(x);
                }
                "nil" => {
                    return Ok(Atom::new(T));
                }
                "isnil" => {
                    return Ok(Ap::new(
                        x,
                        Ap::new(Atom::new(T), Ap::new(Atom::new(T), Atom::new(F))),
                    ));
                }
                "car" => {
                    return Ok(Ap::new(x, Atom::new(T)));
                }
                "cdr" => {
                    return Ok(Ap::new(x, Atom::new(F)));
                }
                _ => (),
            }
        } else {
            let func2 = eval(
                func.borrow()
                    .func()
                    .ok_or_else(|| "func expected on func of try_eval")?,
                functions,
            )?;
            let y = func
                .borrow()
                .arg()
                .ok_or_else(|| "arg expected on func of try_eval")?;
            if let Some(name) = func2.clone().borrow().name().as_ref() {
                match *name {
                    "t" => {
                        return Ok(y);
                    }
                    "f" => {
                        return Ok(x);
                    }
                    "add" => {
                        return Ok(Atom::new(
                            as_num(eval(x, functions)?)? + as_num(eval(y, functions)?)?,
                        ));
                    }
                    "mul" => {
                        return Ok(Atom::new(
                            as_num(eval(x, functions)?)? * as_num(eval(y, functions)?)?,
                        ));
                    }
                    "div" => {
                        return Ok(Atom::new(
                            as_num(eval(y, functions)?)? / as_num(eval(x, functions)?)?,
                        ));
                    }
                    "eq" => {
                        let are_equal =
                            as_num(eval(x, functions)?)? == as_num(eval(y, functions)?)?;
                        return Ok(if are_equal {
                            Atom::new(T)
                        } else {
                            Atom::new(F)
                        });
                    }
                    "lt" => {
                        let is_less_than =
                            as_num(eval(y, functions)?)? < as_num(eval(x, functions)?)?;
                        return Ok(if is_less_than {
                            Atom::new(T)
                        } else {
                            Atom::new(F)
                        });
                    }
                    "cons" => {
                        return Ok(eval_cons(y, x, functions)?);
                    }
                    _ => (),
                }
            } else {
                let func3 = eval(
                    func2
                        .borrow()
                        .func()
                        .ok_or_else(|| "func expected on func2 of try_eval")?,
                    functions,
                )?;
                let z = func2
                    .borrow()
                    .arg()
                    .ok_or_else(|| "arg expected on func2 of try_eval")?;
                if let Some(name) = func3.clone().borrow().name().as_ref() {
                    match *name {
                        "s" => return Ok(Ap::new(Ap::new(z, x.clone()), Ap::new(y, x))),
                        "c" => return Ok(Ap::new(Ap::new(z, x), y)),
                        "b" => return Ok(Ap::new(z, Ap::new(y, x))),
                        "cons" => return Ok(Ap::new(Ap::new(x, z), y)),
                        _ => (),
                    }
                }
            }
        }
    }

    Ok(expr)
}

fn eval_cons(
    head: ExprRef,
    tail: ExprRef,
    functions: &HashMap<String, ExprRef>,
) -> Result<ExprRef, String> {
    let res = Ap::new(
        Ap::new(Atom::new(CONS), eval(head, functions)?),
        eval(tail, functions)?,
    );
    res.borrow_mut().set_evaluated(res.clone())?;

    Ok(res)
}

fn vectorize_points_expr(points_expr: ExprRef) -> Result<Vec<(i64, i64)>, String> {
    let mut result = vec![];

    let flattened: Vec<ExprRef> = get_list_items_from_expr(points_expr)?;
    for expr in flattened.into_iter() {
        result.push(flatten_point(expr)?);
    }

    Ok(result)
}

fn print_images(images: ExprRef) {
    let image_lists = get_list_items_from_expr(images).unwrap();
    for point_list_expr in image_lists.iter() {
        let points = vectorize_points_expr(point_list_expr.clone());
        println!("Image points {:?}", points);
    }
    panic!("print_images is not yet implemented, tried to print");
}

fn request_click_from_user() -> Point {
    panic!("request_click_from_user is not yet implemented");
}

fn main() {
    let functions: HashMap<String, ExprRef> = load_function_definitions("galaxy.txt").unwrap();

    // See https://message-from-space.readthedocs.io/en/latest/message39.html
    let mut state: ExprRef = Atom::new(NIL);
    let mut point = Point { x: 0, y: 0 };

    loop {
        let click = Ap::new(
            Ap::new(Atom::new(CONS), Atom::new(point.x)),
            Atom::new(point.y),
        );
        let (new_state, images) = interact(state, click, &functions);
        print_images(images);
        point = request_click_from_user();
        state = new_state;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn str_to_expr(text: &str) -> Result<ExprRef, String> {
        let tokens: Vec<&str> = text.split(' ').filter(|s| !s.is_empty()).collect();
        let (expr, remainder) = deserialize(tokens)?;
        if remainder.len() > 0 {
            return Err(format!(
                "Function body did not cleanly parse, tokens remained: {:?}",
                remainder
            ));
        }
        Ok(expr)
    }

    fn assert_equal(result: ExprRef, expectation: ExprRef) {
        assert!(
            result.borrow().equals(expectation.clone()),
            format!("{:?} != {:?}", result, expectation)
        );
    }

    #[test]
    fn pseudo_addition() {
        let result = eval(str_to_expr("ap ap add 2 3").unwrap(), &hashmap! {}).unwrap();

        let expected = Atom::new(5);
        assert_equal(result, expected);
    }

    #[test]
    fn pseudo_division() {
        let result = eval(str_to_expr("ap ap div -9 4").unwrap(), &hashmap! {}).unwrap();

        let expected = Atom::new(-2);
        assert_equal(result, expected);
    }
}
