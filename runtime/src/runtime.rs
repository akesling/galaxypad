use lazy_static::lazy_static;
use maplit::{hashmap, hashset};

use std::collections::{HashMap, HashSet};
use std::fmt::Debug;
use std::ptr;

use gc::{Finalize, Gc, GcCell, Trace};

struct Constants {
    cons: ExprRef,
    t: ExprRef,
    f: ExprRef,
    nil: ExprRef,
}

#[derive(Debug, PartialEq, Clone, Eq, Hash, Trace, Finalize)]
enum Name {
    Function(u32),
    Variable(u32),
    Int(i64),

    // Bookkeeping
    EagerThunk1,
    EagerThunk2,
    LazyThunk1,
    LazyThunk2,
    LazyThunk3,

    // Operators
    Add,
    I,
    T,
    F,
    Mul,
    Div,
    Eq,
    Lt,
    Neg,
    S,
    C,
    B,
    Cons,
    Car,
    Cdr,
    Nil,
    Isnil,
}

lazy_static! {
    static ref ONE_ARG_OPERATORS: HashSet<Name> = hashset!{
         Name::I,
         Name::Neg,
         Name::Car,
         Name::Cdr,
         Name::Nil,
         Name::Isnil,
    };
    static ref TWO_ARG_OPERATORS: HashSet<Name> = hashset!{
         Name::Add,
         Name::T,
         Name::F,
         Name::Mul,
         Name::Div,
         Name::Eq,
         Name::Lt,
         Name::Cons,
    };
    static ref THREE_ARG_OPERATORS: HashSet<Name> = hashset!{
         Name::S,
         Name::C,
         Name::B,
         Name::Cons,
    };
    static ref OPERATOR_ATOMS: HashMap<&'static str, Name> = hashmap!{
        "add" => Name::Add,
        //"inc",
        //"dec",
        "i" => Name::I,
        "t" => Name::T,
        "f" => Name::F,
        "mul" => Name::Mul,
        "div" => Name::Div,
        "eq" => Name::Eq,
        "lt" => Name::Lt,
        "neg" => Name::Neg,
        "s" => Name::S,
        "c" => Name::C,
        "b" => Name::B,
        //"pwr2",
        "cons" => Name::Cons,
        "car" => Name::Car,
        "cdr" => Name::Cdr,
        "nil" => Name::Nil,
        "isnil" => Name::Isnil,
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

type ExprRef = Gc<GcCell<Expr>>;

#[derive(Trace, Finalize)]
enum Expr {
    Atom(Atom),
    Ap(Ap),
}

impl Expr {
    #[allow(dead_code)]
    fn is_atom(&self) -> bool {
        match *self {
            Expr::Atom(_) => true,
            Expr::Ap(_) => false,
        }
    }

    #[allow(dead_code)]
    fn is_ap(&self) -> bool {
        match *self {
            Expr::Atom(_) => false,
            Expr::Ap(_) => true,
        }
    }

    fn name(&self) -> Option<&Name> {
        match *self {
            Expr::Atom(ref atom) => Some(&atom.name),
            Expr::Ap(_) => None,
        }
    }

    fn func(&self) -> Option<ExprRef> {
        match *self {
            Expr::Atom(_) => None,
            Expr::Ap(ref ap) => Some(ap.func()),
        }
    }

    fn arg(&self) -> Option<ExprRef> {
        match *self {
            Expr::Atom(_) => None,
            Expr::Ap(ref ap) => Some(ap.arg()),
        }
    }

    fn evaluated(&self) -> Option<ExprRef> {
        match *self {
            Expr::Atom(ref atom) => atom.evaluated(),
            Expr::Ap(ref ap) => ap.evaluated(),
        }
    }

    // NOTE(akesling): Beware memory leaks through circular dependencies on evaluated results!
    fn set_evaluated(&mut self, other: ExprRef) -> Result<(), String> {
        match *self {
            Expr::Atom(ref mut atom) => atom.set_evaluated(other),
            Expr::Ap(ref mut ap) => ap.set_evaluated(other),
        }
    }

    fn equals(&self, other: ExprRef) -> bool {
        match *self {
            Expr::Atom(ref atom) => atom.equals(other),
            Expr::Ap(ref ap) => ap.equals(other),
        }
    }
}

impl std::fmt::Display for Expr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match *self {
            Expr::Atom(ref atom) => write!(f, "Atom({:?})", atom.name),
            Expr::Ap(ref ap) => write!(f, "Ap({}, {})", ap.func.borrow(), ap.arg.borrow()),
        }
    }
}

impl Debug for Expr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match *self {
            Expr::Atom(ref atom) => f
                .debug_struct("Atom")
                .field("name", &atom.name)
                .field("evaluated", &atom.evaluated().is_some())
                .finish(),
            Expr::Ap(ref ap) => f
                .debug_struct("Ap")
                .field("func", &ap.func().borrow())
                .field("arg", &ap.arg().borrow())
                .field("evaluated", &ap.evaluated().is_some())
                .finish(),
        }
    }
}

#[derive(Trace, Finalize)]
struct Atom {
    evaluated: Option<ExprRef>,

    name: Name,
}

impl std::fmt::Display for Atom {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Atom({:?})", self.name)?;
        Ok(())
    }
}

impl Atom {
    #[allow(clippy::new_ret_no_self)]
    fn new(name: Name) -> ExprRef {
        Gc::new(GcCell::new(Expr::Atom(Atom {
            name,
            evaluated: None,
        })))
    }

    fn evaluated(&self) -> Option<ExprRef> {
        match &self.evaluated {
            Some(expr_ref) => Some(expr_ref.clone()),
            None => None,
        }
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        self.evaluated = Some(expr);
        Ok(())
    }

    fn equals(&self, other: ExprRef) -> bool {
        match other.borrow().name() {
            Some(name) => self.name == *name,
            None => false,
        }
    }
}

#[derive(Trace, Finalize)]
struct Ap {
    evaluated: Option<ExprRef>,

    func: ExprRef,
    arg: ExprRef,
}

impl Ap {
    #[allow(clippy::new_ret_no_self)]
    fn new(func: ExprRef, arg: ExprRef) -> ExprRef {
        Gc::new(GcCell::new(Expr::Ap(Ap {
            func,
            arg,
            evaluated: None,
        })))
    }
}

impl std::fmt::Display for Ap {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Ap({}, {})", self.func.borrow(), self.arg.borrow())?;
        Ok(())
    }
}

impl Debug for Ap {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Ap")
            .field("func", &self.func.borrow())
            .field("arg", &self.arg.borrow())
            .field("evaluated", &self.evaluated().is_some())
            .finish()
    }
}

impl Ap {
    fn func(&self) -> ExprRef {
        self.func.clone()
    }

    fn arg(&self) -> ExprRef {
        self.arg.clone()
    }

    fn evaluated(&self) -> Option<ExprRef> {
        match &self.evaluated {
            Some(expr_ref) => Some(expr_ref.clone()),
            None => None,
        }
    }

    fn set_evaluated(&mut self, expr: ExprRef) -> Result<(), String> {
        self.evaluated = Some(expr);
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

#[derive(Default, Debug)]
pub struct Point {
    pub x: i64,
    pub y: i64,
}

fn parse_token(candidate_token: &str, stack: &mut Vec<ExprRef>) -> Result<ExprRef, String> {
    if candidate_token == "ap" {
        let left = stack
            .pop()
            .ok_or_else(|| "Left operand for Ap was missing on stack")?;
        let right = stack
            .pop()
            .ok_or_else(|| "Right operand for Ap was missing on stack")?;
        return Ok(Ap::new(left, right));
    }

    if let Some(token_name) = OPERATOR_ATOMS.get(candidate_token) {
        return Ok(Atom::new(token_name.clone()));
    }

    if let Ok(i) = candidate_token.parse::<i64>() {
        return Ok(Atom::new(Name::Int(i)));
    }

    if candidate_token.starts_with(':') {
        if let Ok(i) = candidate_token[1..].parse::<u32>() {
            return Ok(Atom::new(Name::Function(i)));
        }
    }

    if candidate_token.starts_with('x') {
        if let Ok(i) = candidate_token[1..].parse::<u32>() {
            return Ok(Atom::new(Name::Variable(i)));
        }
    }

    Err(format!("Could not parse '{}'", candidate_token))
}

fn deserialize(tokens: &[&str]) -> Result<ExprRef, String> {
    if tokens.is_empty() {
        return Err("Attempt to deserialize the empty token stream failed".to_owned());
    }

    let mut cursor = tokens.len();
    let mut stack: Box<Vec<ExprRef>> = Box::new(vec![]);
    while cursor > 0 {
        let expr = parse_token(tokens[cursor - 1], &mut stack)?;
        stack.push(expr);
        cursor -= 1;
    }

    if stack.len() > 1 {
        return Err(format!(
            "Deserialization produced more than one root value {:?}",
            stack,
        ));
    }

    Ok(stack
        .pop()
        .ok_or_else(|| "No value left on deserialization stack to return.")?)
}

/// Loads a function definition, which must be of the form:
/// <name> = <body expr>
fn load_function(line: &str) -> Result<(u32, ExprRef), String> {
    let left_and_right: Box<Vec<&str>> =
        Box::new(line.split('=').filter(|s| !s.is_empty()).collect());
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
    let function_name = left_tokens[0][1..].parse::<u32>().unwrap();

    let right_tokens: Box<Vec<&str>> = Box::new(
        left_and_right[1]
            .split(' ')
            .filter(|s| !s.is_empty())
            .collect(),
    );
    assert!(!right_tokens.is_empty(), "Function body was of length zero");
    let function_body = deserialize(right_tokens.as_slice())?;

    Ok((function_name, function_body))
}

/// Opens the given filename and attempts to load each line as a function
/// definition (pretty much just for galaxy.txt)
fn load_function_definitions(
    script_contents: &str,
    functions: &mut HashMap<u32, ExprRef>,
) -> Result<(), String> {
    let lines = Box::new(script_contents.split('\n'));
    for line in lines {
        if line.is_empty() {
            continue;
        }
        let (name, expr) = load_function(line)?;

        functions.insert(name, expr);
    }

    Ok(())
}

fn interact(
    state: ExprRef,
    event: ExprRef,
    functions: &HashMap<u32, ExprRef>,
    constants: &Constants,
    describe_progress: &dyn Fn(&str),
) -> (ExprRef, ExprRef) {
    // See https://message-from-space.readthedocs.io/en/latest/message38.html
    let expr: ExprRef = Ap::new(
        // Galaxy function is :841463
        Ap::new(Atom::new(Name::Function(841463)), state),
        event,
    );
    describe_progress("Evaluating :galaxy...");
    let res: ExprRef = eval(expr, functions, constants).unwrap();
    // Note: res will be modulatable here (consists of cons, nil and numbers only)
    describe_progress("Parsing resulting items...");
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

    describe_progress("Recursing into interact...");
    interact(
        new_state,
        send_to_alien_proxy(data),
        functions,
        constants,
        describe_progress,
    )
}

fn send_to_alien_proxy(_expr: ExprRef) -> ExprRef {
    panic!("send_to_alien_proxy is not yet implemented");
}

fn as_num(expr: ExprRef) -> Result<i64, String> {
    if let Some(name) = expr.borrow().name() {
        return match *name {
            Name::Int(i) => Ok(i),
            Name::T => Ok(1),
            Name::F => Ok(0),
            _ => Err(format!("Not a number: {:?}", expr)),
        };
    }
    Err(format!("Not a number: {:?}", expr))
}

fn flatten_point(points_expr: ExprRef) -> Result<(i64, i64), String> {
    if let Some(name) = points_expr.borrow().name().as_ref() {
        return Err(format!("First item in pair was atom({:?}) not Ap", name));
    }

    let second = points_expr
        .borrow()
        .func()
        .ok_or_else(|| "func expected on points_expr of flatten_point")?;
    if let Some(name) = second.borrow().name().as_ref() {
        return Err(format!(
            "Second item in list was non-nil atom({:?}) not Ap",
            name
        ));
    }

    let cons = second
        .borrow()
        .func()
        .ok_or_else(|| "func expected on second of flatten_point")?;
    if let Some(name) = cons.borrow().name() {
        if *name != Name::Cons {
            return Err(format!(
                "Cons-place item in list was atom({:?}) not cons",
                name
            ));
        }
    }

    let first_num = as_num(
        points_expr
            .borrow()
            .arg()
            .ok_or_else(|| "arg expected on points_expr of flatten_point")?,
    )?;
    let second_num = as_num(
        second
            .borrow()
            .arg()
            .ok_or_else(|| "arg expected on second of flatten_point")?,
    )?;
    Ok((second_num, first_num))
}

fn get_list_items_from_expr(expr: ExprRef) -> Result<Vec<ExprRef>, String> {
    if let Some(name) = expr.borrow().name() {
        if name == &Name::Nil {
            return Ok(vec![expr.clone()]);
        }

        return Err(format!(
            "First item in list was non-nil atom({:?}) not Ap",
            name
        ));
    }

    let second = expr
        .borrow()
        .func()
        .ok_or_else(|| "func expected on func of get_list_items_from_expr")?;
    if let Some(name) = second.borrow().name() {
        return Err(format!(
            "Second item in list was non-nil atom({:?}) not Ap",
            name
        ));
    }

    let cons = second
        .borrow()
        .func()
        .ok_or_else(|| "func expected on second of get_list_items_from_expr")?;
    if let Some(name) = cons.borrow().name() {
        if name != &Name::Cons {
            return Err(format!(
                "Cons-place item in list was atom({:?}) not cons",
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
    if let Some(name) = next.clone().borrow().name() {
        if name == &Name::Nil {
            Ok(flattened)
        } else {
            Err(format!(
                "get_list_items_from_expr somehow got a non-nil end node in a list {:?}",
                name
            ))
        }
    } else {
        flattened.extend(get_list_items_from_expr(next)?);

        Ok(flattened)
    }
}

fn eval_iterative(
    expr: ExprRef,
    functions: &HashMap<u32, ExprRef>,
    constants: &Constants,
) -> Result<ExprRef, String> {
    if let Some(x) = expr.borrow().evaluated() {
        return Ok(x);
    }

    let initial_expr = expr.clone();
    let mut current_expr = expr;
    loop {
        let mut stack: Vec<ExprRef> = vec![current_expr.clone()];
        let result: Option<ExprRef>;
        let mut args: Vec<ExprRef> = vec![];
        loop {
            let mut next_to_evaluate = stack.pop().unwrap();
            if stack.is_empty() && next_to_evaluate.borrow().evaluated().is_some() {
                result = Some(next_to_evaluate);
                break;
            }

            while next_to_evaluate.borrow().evaluated().is_some() {
                args.push(next_to_evaluate);
                next_to_evaluate = stack.pop().unwrap();
            }

            next_to_evaluate = match *next_to_evaluate.clone().borrow() {
                Expr::Atom(ref atom) => match atom.name {
                    Name::EagerThunk1 => Ap::new(args.pop().unwrap(), args.pop().unwrap()),
                    Name::EagerThunk2 => Ap::new(
                        Ap::new(args.pop().unwrap(), args.pop().unwrap()),
                        args.pop().unwrap(),
                    ),
                    _ => next_to_evaluate,
                },
                _ => next_to_evaluate,
            };

            match *next_to_evaluate.clone().borrow() {
                Expr::Atom(Atom {
                    name: Name::Function(ref id),
                    evaluated: _,
                }) => {
                    if let Some(f) = functions.get(id) {
                        stack.push(f.clone());
                        continue;
                    } else {
                        return Err(format!(
                            "Unexpected function symbol encountered {} in expression {}",
                            id,
                            next_to_evaluate.borrow()
                        ));
                    }
                }
                Expr::Atom(Atom {
                    name: Name::Variable(id),
                    evaluated: _,
                }) => {
                    let res = Atom::new(Name::Variable(id));
                    res.borrow_mut().set_evaluated(res.clone())?;
                    stack.push(res);
                    continue;
                }
                Expr::Ap(ref ap1) => {
                    // println!("Evaluating ap1 {:?}", ap1);
                    let x = ap1.arg();
                    match *ap1.func().clone().borrow() {
                        Expr::Atom(ref atom) => match (*atom).name {
                            Name::Function(ref id) => {
                                if let Some(f) = functions.get(id) {
                                    stack.push(Ap::new(Atom::new(Name::LazyThunk1), ap1.arg()));
                                    stack.push(f.clone());
                                    continue;
                                } else {
                                    return Err(format!("Unexpected function symbol encountered {} in expression {}", id, next_to_evaluate.borrow()));
                                }
                            }
                            Name::Variable(id) => {
                                let res = Ap::new(Atom::new(Name::Variable(id)), x);
                                res.borrow_mut().set_evaluated(res.clone())?;
                                stack.push(res);
                                continue;
                            }
                            Name::LazyThunk1 => {
                                stack.push(Ap::new(args.pop().unwrap(), x));
                                continue;
                            }
                            Name::Neg => {
                                if let Some(evaluated) = x.borrow().evaluated() {
                                    let res = Atom::new(Name::Int(-as_num(evaluated)?));
                                    res.borrow_mut().set_evaluated(res.clone())?;
                                    stack.push(res);
                                    continue;
                                }

                                let neg = Atom::new(Name::Neg);
                                neg.borrow_mut().set_evaluated(neg.clone())?;
                                stack.push(Atom::new(Name::EagerThunk1));
                                stack.push(neg);
                                stack.push(x);
                                continue;
                            }
                            Name::I => {
                                // println!("Evaluating identity on {:?}", x.borrow());
                                stack.push(x);
                                continue;
                            }
                            Name::Nil => {
                                stack.push(constants.t.clone());
                                continue;
                            }
                            Name::Isnil => {
                                stack.push(Ap::new(
                                    x,
                                    Ap::new(
                                        constants.t.clone(),
                                        Ap::new(constants.t.clone(), constants.f.clone()),
                                    ),
                                ));
                                continue;
                            }
                            Name::Car => {
                                stack.push(Ap::new(x, constants.t.clone()));
                                continue;
                            }
                            Name::Cdr => {
                                stack.push(Ap::new(x, constants.f.clone()));
                                continue;
                            }
                            _ => (),
                        },
                        Expr::Ap(ref ap2) => {
                            // println!("Evaluating ap2 {:?}", ap2);
                            let y = ap2.arg();
                            match *ap2.func().clone().borrow() {
                                Expr::Atom(ref atom) => match atom.name {
                                    Name::Function(ref id) => {
                                        if let Some(f) = functions.get(id) {
                                            stack.push(Ap::new(
                                                Ap::new(Atom::new(Name::LazyThunk2), y),
                                                x,
                                            ));
                                            stack.push(f.clone());
                                            continue;
                                        } else {
                                            return Err(format!("Unexpected function symbol encountered {} in expression {}", id, next_to_evaluate.borrow()));
                                        }
                                    }
                                    Name::Variable(id) => {
                                        let res =
                                            Ap::new(Ap::new(Atom::new(Name::Variable(id)), y), x);
                                        res.borrow_mut().set_evaluated(res.clone())?;
                                        stack.push(res);
                                        continue;
                                    }
                                    Name::LazyThunk2 => {
                                        stack.push(Ap::new(Ap::new(args.pop().unwrap(), y), x));
                                        continue;
                                    }
                                    Name::T => {
                                        stack.push(y);
                                        continue;
                                    }
                                    Name::F => {
                                        stack.push(x);
                                        continue;
                                    }
                                    Name::Add => {
                                        if let Some(x_evaluated) = x.borrow().evaluated() {
                                            if let Some(y_evaluated) = y.borrow().evaluated() {
                                                let res = Atom::new(Name::Int(
                                                    as_num(y_evaluated)? + as_num(x_evaluated)?,
                                                ));
                                                res.borrow_mut().set_evaluated(res.clone())?;
                                                stack.push(res);
                                                continue;
                                            }
                                        }

                                        let add = Atom::new(Name::Add);
                                        add.borrow_mut().set_evaluated(add.clone())?;
                                        stack.push(Atom::new(Name::EagerThunk2));
                                        stack.push(add);
                                        stack.push(x);
                                        stack.push(y);
                                        continue;
                                    }
                                    Name::Mul => {
                                        if let Some(x_evaluated) = x.borrow().evaluated() {
                                            if let Some(y_evaluated) = y.borrow().evaluated() {
                                                let res = Atom::new(Name::Int(
                                                    as_num(y_evaluated)? * as_num(x_evaluated)?,
                                                ));
                                                res.borrow_mut().set_evaluated(res.clone())?;
                                                stack.push(res);
                                                continue;
                                            }
                                        }

                                        let mul = Atom::new(Name::Mul);
                                        mul.borrow_mut().set_evaluated(mul.clone())?;
                                        stack.push(Atom::new(Name::EagerThunk2));
                                        stack.push(mul);
                                        stack.push(x);
                                        stack.push(y);
                                        continue;
                                    }
                                    Name::Div => {
                                        if let Some(x_evaluated) = x.borrow().evaluated() {
                                            if let Some(y_evaluated) = y.borrow().evaluated() {
                                                let res = Atom::new(Name::Int(
                                                    as_num(y_evaluated)? / as_num(x_evaluated)?,
                                                ));
                                                res.borrow_mut().set_evaluated(res.clone())?;
                                                stack.push(res);
                                                continue;
                                            }
                                        }

                                        let div = Atom::new(Name::Div);
                                        div.borrow_mut().set_evaluated(div.clone())?;
                                        stack.push(Atom::new(Name::EagerThunk2));
                                        stack.push(div);
                                        stack.push(y);
                                        stack.push(x);
                                        continue;
                                    }
                                    Name::Eq => {
                                        if let Some(x_evaluated) = x.borrow().evaluated() {
                                            if let Some(y_evaluated) = y.borrow().evaluated() {
                                                let are_equal =
                                                    as_num(y_evaluated)? == as_num(x_evaluated)?;
                                                stack.push(if are_equal {
                                                    constants.t.clone()
                                                } else {
                                                    constants.f.clone()
                                                });
                                                continue;
                                            }
                                        }

                                        let eq = Atom::new(Name::Eq);
                                        eq.borrow_mut().set_evaluated(eq.clone())?;
                                        stack.push(Atom::new(Name::EagerThunk2));
                                        stack.push(eq);
                                        stack.push(y);
                                        stack.push(x);
                                        continue;
                                    }
                                    Name::Lt => {
                                        if let Some(x_evaluated) = x.borrow().evaluated() {
                                            if let Some(y_evaluated) = y.borrow().evaluated() {
                                                let is_less_than =
                                                    as_num(y_evaluated)? < as_num(x_evaluated)?;
                                                stack.push(if is_less_than {
                                                    constants.t.clone()
                                                } else {
                                                    constants.f.clone()
                                                });
                                                continue;
                                            }
                                        }

                                        let lt = Atom::new(Name::Lt);
                                        lt.borrow_mut().set_evaluated(lt.clone())?;
                                        stack.push(Atom::new(Name::EagerThunk2));
                                        stack.push(lt);
                                        stack.push(y);
                                        stack.push(x);
                                        continue;
                                    }
                                    Name::Cons => {
                                        if let Some(x_evaluated) = x.borrow().evaluated() {
                                            if let Some(y_evaluated) = y.borrow().evaluated() {
                                                let inner =
                                                    Ap::new(constants.cons.clone(), y_evaluated);
                                                inner.borrow_mut().set_evaluated(inner.clone())?;
                                                let res = Ap::new(inner, x_evaluated);
                                                res.borrow_mut().set_evaluated(res.clone())?;
                                                stack.push(res);
                                                continue;
                                            }
                                        }

                                        let cons = Atom::new(Name::Cons);
                                        cons.borrow_mut().set_evaluated(cons.clone())?;
                                        stack.push(Atom::new(Name::EagerThunk2));
                                        stack.push(cons);
                                        stack.push(y);
                                        stack.push(x);
                                        continue;
                                    }
                                    _ => {
                                        if !TWO_ARG_OPERATORS.contains(&atom.name)
                                            && !THREE_ARG_OPERATORS.contains(&atom.name)
                                        {
                                            // None of the two-arg operators matched, try
                                            // unwrapping the outermost ap to evaluate.
                                            stack.push(Ap::new(Atom::new(Name::LazyThunk1), x));
                                            stack.push(next_to_evaluate.borrow().func().unwrap());
                                            continue;
                                        }
                                    }
                                },
                                Expr::Ap(ref ap3) => {
                                    // println!("Evaluating ap3 {:?}", ap3);
                                    let z = ap3.arg();
                                    match *ap3.func().clone().borrow() {
                                        Expr::Atom(ref atom) => match atom.name {
                                            Name::Function(ref id) => {
                                                // println!("Found ap3 placeholder {}", name);
                                                if let Some(f) = functions.get(id) {
                                                    stack.push(Ap::new(
                                                        Ap::new(
                                                            Ap::new(Atom::new(Name::LazyThunk3), z),
                                                            y,
                                                        ),
                                                        x,
                                                    ));
                                                    stack.push(f.clone());
                                                    continue;
                                                } else {
                                                    return Err(format!("Unexpected function symbol encountered {} in expression {}", id, next_to_evaluate.borrow()));
                                                }
                                            }
                                            Name::Variable(id) => {
                                                // println!("Found ap3 placeholder {}", name);
                                                let res = Ap::new(
                                                    Ap::new(
                                                        Ap::new(Atom::new(Name::Variable(id)), z),
                                                        y,
                                                    ),
                                                    x,
                                                );
                                                res.borrow_mut().set_evaluated(res.clone())?;
                                                stack.push(res);
                                                continue;
                                            }
                                            Name::LazyThunk3 => {
                                                stack.push(Ap::new(
                                                    Ap::new(Ap::new(args.pop().unwrap(), z), y),
                                                    x,
                                                ));
                                                continue;
                                            }
                                            Name::S => {
                                                stack.push(Ap::new(
                                                    Ap::new(z, x.clone()),
                                                    Ap::new(y, x),
                                                ));
                                                continue;
                                            }
                                            Name::C => {
                                                stack.push(Ap::new(Ap::new(z, x), y));
                                                continue;
                                            }
                                            Name::B => {
                                                stack.push(Ap::new(z, Ap::new(y, x)));
                                                continue;
                                            }
                                            Name::Cons => {
                                                // println!("Processing ap3 cons");
                                                stack.push(Ap::new(Ap::new(x, z), y));
                                                continue;
                                            }
                                            _ => {
                                                // None of the three-arg combinators matched, try
                                                // unwrapping the outermost ap to evaluate.
                                                stack.push(Ap::new(Atom::new(Name::LazyThunk1), x));
                                                stack.push(
                                                    next_to_evaluate.borrow().func().unwrap(),
                                                );
                                                continue;
                                            }
                                        },
                                        _ => {
                                            // More than three ap's are applied, try unwrapping the
                                            // outermost ap to evaluate.
                                            stack.push(Ap::new(Atom::new(Name::LazyThunk1), x));
                                            stack.push(next_to_evaluate.borrow().func().unwrap());
                                            continue;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                _ => (),
            }

            next_to_evaluate
                .borrow_mut()
                .set_evaluated(next_to_evaluate.clone())?;
            stack.push(next_to_evaluate);
        }

        if let Some(res) = result {
            if ptr::eq(current_expr.as_ref(), res.as_ref()) || res.borrow().equals(current_expr) {
                initial_expr.borrow_mut().set_evaluated(res.clone())?;
                return Ok(res);
            }
            current_expr = res;
        } else {
            return Err("Result failed for some reason".to_owned());
        }
    }
}

fn eval(
    expr: ExprRef,
    functions: &HashMap<u32, ExprRef>,
    constants: &Constants,
) -> Result<ExprRef, String> {
    if let Some(x) = expr.borrow().evaluated() {
        return Ok(x);
    }

    let initial_expr = expr.clone();
    let mut current_expr = expr;
    loop {
        let result = try_eval(current_expr.clone(), functions, constants)?;
        if ptr::eq(current_expr.as_ref(), result.as_ref()) || result.borrow().equals(current_expr) {
            initial_expr.borrow_mut().set_evaluated(result.clone())?;
            return Ok(result);
        }
        current_expr = result;
    }
}

#[allow(clippy::all)]
fn try_eval(
    expr: ExprRef,
    functions: &HashMap<u32, ExprRef>,
    constants: &Constants,
) -> Result<ExprRef, String> {
    if let Some(x) = expr.borrow().evaluated() {
        return Ok(x);
    }

    match *expr.borrow() {
        Expr::Atom(Atom {
            name: Name::Function(ref id),
            evaluated: _,
        }) => {
            if let Some(f) = functions.get(id) {
                return Ok(f.clone());
            }
        }
        Expr::Ap(_) => {
            let func = eval(
                expr.borrow()
                    .func()
                    .ok_or_else(|| "func expected on expr of try_eval")?,
                functions,
                constants,
            )?;
            let x = expr
                .borrow()
                .arg()
                .ok_or_else(|| "arg expected on expr of try_eval")?;
            if let Some(name) = func.clone().borrow().name() {
                match name {
                    Name::Neg => {
                        return Ok(Atom::new(Name::Int(-as_num(eval(
                            x, functions, constants,
                        )?)?)));
                    }
                    Name::I => {
                        return Ok(x);
                    }
                    Name::Nil => {
                        return Ok(constants.t.clone());
                    }
                    Name::Isnil => {
                        return Ok(Ap::new(
                            x,
                            Ap::new(
                                constants.t.clone(),
                                Ap::new(constants.t.clone(), constants.f.clone()),
                            ),
                        ));
                    }
                    Name::Car => {
                        return Ok(Ap::new(x, constants.t.clone()));
                    }
                    Name::Cdr => {
                        return Ok(Ap::new(x, constants.f.clone()));
                    }
                    _ => (),
                }
            } else {
                let func2 = eval(
                    func.borrow()
                        .func()
                        .ok_or_else(|| "func expected on func of try_eval")?,
                    functions,
                    constants,
                )?;
                let y = func
                    .borrow()
                    .arg()
                    .ok_or_else(|| "arg expected on func of try_eval")?;
                if let Some(name) = func2.clone().borrow().name() {
                    match name {
                        Name::T => {
                            return Ok(y);
                        }
                        Name::F => {
                            return Ok(x);
                        }
                        Name::Add => {
                            return Ok(Atom::new(Name::Int(
                                as_num(eval(x, functions, constants)?)?
                                    + as_num(eval(y, functions, constants)?)?,
                            )));
                        }
                        Name::Mul => {
                            return Ok(Atom::new(Name::Int(
                                as_num(eval(x, functions, constants)?)?
                                    * as_num(eval(y, functions, constants)?)?,
                            )));
                        }
                        Name::Div => {
                            return Ok(Atom::new(Name::Int(
                                as_num(eval(y, functions, constants)?)?
                                    / as_num(eval(x, functions, constants)?)?,
                            )));
                        }
                        Name::Eq => {
                            let are_equal = as_num(eval(x, functions, constants)?)?
                                == as_num(eval(y, functions, constants)?)?;
                            return Ok(if are_equal {
                                constants.t.clone()
                            } else {
                                constants.f.clone()
                            });
                        }
                        Name::Lt => {
                            let is_less_than = as_num(eval(y, functions, constants)?)?
                                < as_num(eval(x, functions, constants)?)?;
                            return Ok(if is_less_than {
                                constants.t.clone()
                            } else {
                                constants.f.clone()
                            });
                        }
                        Name::Cons => {
                            return Ok(_eval_cons(y, x, functions, constants)?);
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
                        constants,
                    )?;
                    let z = func2
                        .borrow()
                        .arg()
                        .ok_or_else(|| "arg expected on func2 of try_eval")?;
                    if let Some(name) = func3.clone().borrow().name() {
                        match name {
                            Name::S => return Ok(Ap::new(Ap::new(z, x.clone()), Ap::new(y, x))),
                            Name::C => return Ok(Ap::new(Ap::new(z, x), y)),
                            Name::B => return Ok(Ap::new(z, Ap::new(y, x))),
                            Name::Cons => return Ok(Ap::new(Ap::new(x, z), y)),
                            _ => (),
                        }
                    }
                }
            }
        }
        _ => (),
    }

    Ok(expr)
}

fn _eval_cons(
    head: ExprRef,
    tail: ExprRef,
    functions: &HashMap<u32, ExprRef>,
    constants: &Constants,
) -> Result<ExprRef, String> {
    let res = Ap::new(
        Ap::new(constants.cons.clone(), eval(head, functions, constants)?),
        eval(tail, functions, constants)?,
    );
    res.borrow_mut().set_evaluated(res.clone())?;

    Ok(res)
}

fn vectorize_points_expr(list_of_points_expr: ExprRef) -> Result<Vec<(i64, i64)>, String> {
    let mut result = vec![];

    let pairs: Vec<ExprRef> = get_list_items_from_expr(list_of_points_expr)?;
    for expr in pairs.into_iter() {
        if !expr.borrow().equals(Atom::new(Name::Nil)) {
            result.push(flatten_point(expr)?);
        }
    }

    Ok(result)
}

#[allow(dead_code)]
fn print_images(point_lists: Vec<Vec<(i64, i64)>>) {
    const SIZE: (u32, u32) = (1024, 1024);
    const CENTER: (u32, u32) = (SIZE.0 / 2, SIZE.1 / 2);
    {
        use draw::*;
        // create a canvas to draw on
        let mut canvas = Canvas::new(SIZE.0, SIZE.1);
        // create a new drawing
        for points in point_lists {
            for p in points {
                let rect = Drawing::new()
                    // give it a shape
                    .with_shape(Shape::Rectangle {
                        width: 1,
                        height: 1,
                    })
                    // give it a cool style
                    .with_style(Style::filled(Color::black()));

                let projected_point = (p.0 as u32 + CENTER.0, p.1 as u32 + CENTER.1);
                canvas
                    .display_list
                    .add(rect.with_xy(projected_point.0 as f32, projected_point.1 as f32));
            }
        }

        // save the canvas as an svg
        //        render::save(
        //            &canvas,
        //            "tests/svg/basic_end_to_end.svg",
        //            SvgRenderer::new(),
        //        )
        //        .expect("Failed to save");
    }
}

#[allow(dead_code)]
fn request_click_from_user() -> Point {
    panic!("request_click_from_user is not yet implemented");
}

fn get_constants() -> Constants {
    Constants {
        t: Atom::new(Name::T),
        f: Atom::new(Name::F),
        cons: Atom::new(Name::Cons),
        nil: Atom::new(Name::Nil),
    }
}

fn iterate(
    state: ExprRef,
    point: &Point,
    constants: &Constants,
    functions: &HashMap<u32, ExprRef>,
    render_to_display: &dyn Fn(Vec<Vec<(i64, i64)>>),
    describe_progress: &dyn Fn(&str),
) -> ExprRef {
    describe_progress("Iterating...");
    let click = Ap::new(
        Ap::new(constants.cons.clone(), Atom::new(Name::Int(point.x))),
        Atom::new(Name::Int(point.y)),
    );
    describe_progress(&format!("Click inflated {:?}", point));

    describe_progress("Executing interact...");
    let (new_state, images) = interact(state, click, &functions, &constants, describe_progress);
    describe_progress("Interact executed");
    let image_lists = get_list_items_from_expr(images).unwrap();
    describe_progress("Image lists parsed");
    let mut points_lists: Vec<Vec<(i64, i64)>> = vec![];
    for point_list_expr in image_lists.iter() {
        points_lists.push(vectorize_points_expr(point_list_expr.clone()).unwrap());
    }

    render_to_display(points_lists);
    new_state
}

pub struct Callback {
    state: ExprRef,
    functions: HashMap<u32, ExprRef>,
    constants: Constants,
}
impl Callback {
    pub fn call(
        &mut self,
        click: Point,
        render_to_display: &dyn Fn(Vec<Vec<(i64, i64)>>),
        describe_progress: &dyn Fn(&str),
    ) {
        self.state = iterate(
            self.state.clone(),
            &click,
            &self.constants,
            &self.functions,
            render_to_display,
            describe_progress,
        );
    }
}

pub fn entry_point(
    render_to_display: &dyn Fn(Vec<Vec<(i64, i64)>>),
    describe_progress: &dyn Fn(&str),
) -> Box<Callback> {
    describe_progress("Entered entrypoint");
    let galaxy_script = Box::new(std::include_str!("../../third_party/numeric_galaxy.txt"));
    describe_progress("Loaded galaxy script");
    let constants = get_constants();
    describe_progress("Loaded constants");

    let mut callback = Box::new(Callback {
        state: constants.nil.clone(),
        functions: HashMap::new(),
        constants,
    });
    describe_progress("Initialized callback");
    load_function_definitions(&galaxy_script, &mut callback.functions).unwrap();
    describe_progress("Parsed functions from galaxy script");
    let bootup_sequence = vec![
        (0, 0),
        (0, 0),
        (0, 0),
        (0, 0),
        (0, 0),
        (0, 0),
        (0, 0),
        (0, 0),
        (8, 4),
        (2, -8),
        (3, 6),
        (0, -14),
        (-4, 10),
        (9, -3),
        (-4, 10),
        (1, 4),
    ];
    for (i, p) in bootup_sequence.iter().enumerate() {
        describe_progress(&format!("Executed iteration {} of bootup sequence", i));
        callback.call(
            Point { x: p.0, y: p.1 },
            render_to_display,
            describe_progress,
        );
    }
    describe_progress("Executed first iteration");

    callback
}

#[allow(dead_code)]
fn main() {
    let mut callback = entry_point(&print_images, &|d| println!("{}", d));
    loop {
        callback.call(request_click_from_user(), &print_images, &|d| {
            println!("{}", d)
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use maplit::hashmap;

    fn str_to_expr(text: &str) -> Result<ExprRef, String> {
        let tokens: Vec<&str> = text.split(' ').filter(|s| !s.is_empty()).collect();
        let expr = deserialize(tokens.as_slice())?;
        Ok(expr)
    }

    fn build_test_functions(text: &str) -> Result<HashMap<u32, ExprRef>, String> {
        text.split('\n')
            .filter(|s| !s.is_empty())
            .map(|line| load_function(line))
            .collect()
    }

    fn assert_expression_evaluates_to(
        expr: &str,
        expected: ExprRef,
        functions: &HashMap<u32, ExprRef>,
    ) {
        let constants = get_constants();
        let parsed = str_to_expr(expr).unwrap();
        let result = eval(parsed, functions, &constants).unwrap();
        assert!(
            result.borrow().equals(expected.clone()),
            format!("{} => {} != {}", expr, result.borrow(), expected.borrow())
        );
    }

    #[test]
    fn application_order_preserved() {
        let functions = hashmap! {};
        assert_expression_evaluates_to(
            "ap ap mul 2 ap ap add 3 4",
            Atom::new(Name::Int(14)),
            &functions,
        );
    }

    #[test]
    fn addition() {
        let functions = hashmap! {};
        assert_expression_evaluates_to(
            "ap ap add ap ap add 2 2 3",
            Atom::new(Name::Int(7)),
            &functions,
        );
        assert_expression_evaluates_to(
            "ap ap add ap ap add 2 ap ap add 3 2 3",
            Atom::new(Name::Int(10)),
            &functions,
        );
        assert_expression_evaluates_to("ap ap add 2 3", Atom::new(Name::Int(5)), &functions);
        assert_expression_evaluates_to("ap ap add 2 -3", Atom::new(Name::Int(-1)), &functions);
        assert_expression_evaluates_to("ap ap add -2 -3", Atom::new(Name::Int(-5)), &functions);
        assert_expression_evaluates_to("ap ap add -2 3", Atom::new(Name::Int(1)), &functions);
        assert_expression_evaluates_to("ap ap add -2 0", Atom::new(Name::Int(-2)), &functions);
        assert_expression_evaluates_to("ap ap add 2 0", Atom::new(Name::Int(2)), &functions);
        assert_expression_evaluates_to("ap ap add 0 -2", Atom::new(Name::Int(-2)), &functions);
        assert_expression_evaluates_to("ap ap add 0 2", Atom::new(Name::Int(2)), &functions);
    }

    #[test]
    fn division() {
        let functions = hashmap! {};
        assert_expression_evaluates_to("ap ap div -9 4", Atom::new(Name::Int(-2)), &functions);
    }

    #[test]
    fn multiplication() {
        let functions = hashmap! {};
        assert_expression_evaluates_to("ap ap mul 10 2", Atom::new(Name::Int(20)), &functions);
    }

    #[test]
    fn cons_pairing() {
        let functions = hashmap! {};
        assert_expression_evaluates_to(
            "ap ap cons x0 x1",
            Ap::new(
                Ap::new(Atom::new(Name::Cons), Atom::new(Name::Variable(0))),
                Atom::new(Name::Variable(1)),
            ),
            &functions,
        );
    }

    #[test]
    fn cons_application() {
        let functions = hashmap! {};
        assert_expression_evaluates_to(
            "ap ap ap cons x0 x1 x2",
            Ap::new(
                Ap::new(Atom::new(Name::Variable(2)), Atom::new(Name::Variable(0))),
                Atom::new(Name::Variable(1)),
            ),
            &functions,
        );
        assert_expression_evaluates_to(
            "ap ap ap ap cons x0 x1 cons x2",
            Ap::new(
                Ap::new(Atom::new(Name::Variable(2)), Atom::new(Name::Variable(0))),
                Atom::new(Name::Variable(1)),
            ),
            &functions,
        );
    }

    #[test]
    fn isnil() {
        let functions = hashmap! {};

        assert_expression_evaluates_to("ap isnil nil", Atom::new(Name::T), &functions);
        assert_expression_evaluates_to("ap isnil ap ap cons x0 x1", Atom::new(Name::F), &functions);
    }

    #[test]
    fn true_combinator() {
        let functions = build_test_functions(
            // Increment and decrement
            ":0 = ap ap c add 1
            :1 = ap ap c add -1",
        )
        .unwrap();
        assert_expression_evaluates_to("ap ap t x0 x1", Atom::new(Name::Variable(0)), &functions);
        assert_expression_evaluates_to("ap ap t x0 x1", Atom::new(Name::Variable(0)), &functions);
        assert_expression_evaluates_to("ap ap t 1 5", Atom::new(Name::Int(1)), &functions);
        assert_expression_evaluates_to("ap ap t t i", Atom::new(Name::T), &functions);
        assert_expression_evaluates_to("ap ap t t ap :0 5", Atom::new(Name::T), &functions);
        assert_expression_evaluates_to("ap ap t ap :0 5 t", Atom::new(Name::Int(6)), &functions);
    }

    #[test]
    fn false_combinator() {
        let functions = hashmap! {};
        assert_expression_evaluates_to("ap ap f x0 x1", Atom::new(Name::Variable(1)), &functions);
    }

    #[test]
    fn identity() {
        let functions = hashmap! {};
        assert_expression_evaluates_to("ap i x0", Atom::new(Name::Variable(0)), &functions);
        assert_expression_evaluates_to("ap i ap i x0", Atom::new(Name::Variable(0)), &functions);
        assert_expression_evaluates_to("ap i i", Atom::new(Name::I), &functions);
    }

    #[test]
    fn equals() {
        let functions = hashmap! {};

        for num in -20..20 {
            let expr_string = format!("ap ap eq {} {}", num, num);
            assert_expression_evaluates_to(&expr_string, Atom::new(Name::T), &functions);
        }

        for num in -20..20 {
            let expr_string = format!("ap ap eq 30 {}", num);
            assert_expression_evaluates_to(&expr_string, Atom::new(Name::F), &functions);
            let expr_string = format!("ap ap eq {} 30 ", num);
            assert_expression_evaluates_to(&expr_string, Atom::new(Name::F), &functions);
            let expr_string = format!("ap ap eq {} -30", num);
            assert_expression_evaluates_to(&expr_string, Atom::new(Name::F), &functions);
            let expr_string = format!("ap ap eq {} -30", num);
            assert_expression_evaluates_to(&expr_string, Atom::new(Name::F), &functions);
        }
        assert_expression_evaluates_to("ap ap eq t f", Atom::new(Name::F), &functions);
        assert_expression_evaluates_to("ap ap eq f t", Atom::new(Name::F), &functions);

        assert_expression_evaluates_to("ap ap eq t ap i t", Atom::new(Name::T), &functions);
        assert_expression_evaluates_to("ap ap eq t ap ap eq t t", Atom::new(Name::T), &functions);
        assert_expression_evaluates_to("ap ap eq ap ap eq t t t", Atom::new(Name::T), &functions);
    }

    #[test]
    fn less_than() {
        let functions = hashmap! {};

        for num in -20..20 {
            let expr_string = format!("ap ap lt {} {}", num - 1, num);
            assert_expression_evaluates_to(&expr_string, Atom::new(Name::T), &functions);
        }
    }

    #[test]
    fn negate() {
        let functions = hashmap! {};

        for num in -20..20 {
            let expr_string = format!("ap neg {}", num);
            assert_expression_evaluates_to(&expr_string, Atom::new(Name::Int(-num)), &functions);
        }
    }

    #[test]
    fn s_combinator() {
        let functions = hashmap! {};
        assert_expression_evaluates_to(
            "ap ap ap s x0 x1 x2",
            Ap::new(
                Ap::new(Atom::new(Name::Variable(0)), Atom::new(Name::Variable(2))),
                Ap::new(Atom::new(Name::Variable(1)), Atom::new(Name::Variable(2))),
            ),
            &functions,
        );
        assert_expression_evaluates_to(
            "ap ap ap s mul ap add 1 6",
            Atom::new(Name::Int(42)),
            &functions,
        );
        assert_expression_evaluates_to(
            "ap ap ap s add ap add 1 1",
            Atom::new(Name::Int(3)),
            &functions,
        );
    }

    #[test]
    fn c_combinator() {
        let functions = hashmap! {};
        assert_expression_evaluates_to(
            "ap ap ap c x0 x1 x2",
            Ap::new(
                Ap::new(Atom::new(Name::Variable(0)), Atom::new(Name::Variable(2))),
                Atom::new(Name::Variable(1)),
            ),
            &functions,
        );
        assert_expression_evaluates_to("ap ap ap c add 1 2", Atom::new(Name::Int(3)), &functions);
    }

    #[test]
    fn b_combinator() {
        let functions = build_test_functions(
            // increment and decrement
            ":0 = ap ap c add 1
            :1 = ap ap c add -1",
        )
        .unwrap();
        assert_expression_evaluates_to("ap ap ap b :0 :1 0", Atom::new(Name::Int(0)), &functions);
        assert_expression_evaluates_to(
            "ap ap ap b x0 x1 x2",
            Ap::new(
                Atom::new(Name::Variable(0)),
                Ap::new(Atom::new(Name::Variable(1)), Atom::new(Name::Variable(2))),
            ),
            &functions,
        );
    }

    #[test]
    fn car() {
        let functions = hashmap! {};
        assert_expression_evaluates_to(
            "ap car ap ap cons x0 x1",
            Atom::new(Name::Variable(0)),
            &functions,
        );
        assert_expression_evaluates_to(
            "ap car x0",
            Ap::new(Atom::new(Name::Variable(0)), Atom::new(Name::T)),
            &functions,
        );
    }

    #[test]
    fn cdr() {
        let functions = hashmap! {};
        assert_expression_evaluates_to(
            "ap cdr ap ap cons x0 x2",
            Atom::new(Name::Variable(2)),
            &functions,
        );
        assert_expression_evaluates_to(
            "ap cdr x0",
            Ap::new(Atom::new(Name::Variable(0)), Atom::new(Name::F)),
            &functions,
        );
    }

    #[test]
    fn nil() {
        let functions = hashmap! {};
        assert_expression_evaluates_to("ap nil x0", Atom::new(Name::T), &functions);
    }

    #[test]
    fn simple_recursion() {
        let functions = build_test_functions(
            ":2000 = ap ap c t :2000
            :1000 = ap f :1000",
        )
        .unwrap();

        assert_expression_evaluates_to("ap :2000 x0", Atom::new(Name::Variable(0)), &functions);
        assert_expression_evaluates_to("ap :1000 x0", Atom::new(Name::Variable(0)), &functions);
    }
}
