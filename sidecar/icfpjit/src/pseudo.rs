use std::collections::HashMap;
use std::rc::Rc;
use std::cell::RefCell;
use std::error::Error;
use std::fmt::Debug;
use std::ptr;

// See video course https://icfpcontest2020.github.io/#/post/2054

type ExprRef = Rc<RefCell<dyn Expr>>;
trait Expr: Debug {
    fn name(&self) -> Option<&str>;
    fn func(&self) -> Option<ExprRef>;
    fn arg(&self) -> Option<ExprRef>;
    fn evaluated(&self) -> Option<ExprRef>;
    fn set_evaluated(&mut self, ExprRef) -> Result<(), String>;
}

#[derive(Default, Debug)]
struct Atom {
    name: String,
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
        Err(format!("Attempted to set Atom to evaluated with value: {:?}", expr))
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
        Err(format!("Attempted to set Atom to evaluated with value: {:?}", expr))
    }
}

#[derive(Debug)]
struct Ap {
    _evaluated: Option<ExprRef>,

    func: ExprRef,
    arg: ExprRef,
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

fn interact(state: ExprRef, event: ExprRef, functions: &HashMap<String, ExprRef>) -> (ExprRef, ExprRef) {
    // See https://message-from-space.readthedocs.io/en/latest/message38.html
    let expr: ExprRef = Rc::new(RefCell::new(Ap{
        func: Rc::new(RefCell::new(Ap{
            func: Rc::new(RefCell::new(Atom{name: "galaxy".to_owned(), ..Default::default()})),
            arg: state.clone(),
            _evaluated: None,
        })),
        arg: event.clone(),
        _evaluated: None,
    }));
    let res: ExprRef = eval(expr, functions).unwrap();
    // Note: res will be modulatable here (consists of cons, nil and numbers only)
    let items = get_list_items_from_expr(res).unwrap();
    if items.len() < 3 {
        panic!("List was of unexpected length {}, expected 3 items", items.len());
    }
    let (flag, newState, data) = (items[0].clone(), items[1].clone(), items[2].clone());
    if (as_num(flag) == 0) {
        return (newState, data);
    }
    return interact(newState, send_to_alien_proxy(data), functions);
}

fn send_to_alien_proxy(expr: ExprRef) -> ExprRef {
    panic!("send_to_alien_proxy is not yet implemented");
}

fn as_num(expr: ExprRef) -> i64 {
    panic!("as_num is not yet implemented");
}

fn get_list_items_from_expr(expr: ExprRef) -> Result<Vec<ExprRef>, String> {
    panic!("Eval is not yet implemented");
}

fn eval(expr: ExprRef, functions: &HashMap<String, ExprRef>) -> Result<ExprRef, String> {
    match expr.borrow().evaluated() {
        Some(expr) => {
            panic!("Eval is not yet implemented");
        },
        None => {
            let mut current_expr = expr.clone();
            loop {
                let result = try_eval(current_expr.clone(), functions)?;
                if ptr::eq(current_expr.as_ref(), result.as_ref()) {
                    current_expr.borrow_mut().set_evaluated(result.clone())?;
                    return Ok(result);
                } else {
                    current_expr = result.clone();
                }
            }
        }
    }
}

fn try_eval(expr: ExprRef, functions: &HashMap<String, ExprRef>) -> Result<ExprRef, String> {
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
                let func = eval(expr.clone(), functions);
        //        Expr x = expr.Arg
        //        if (fun is Atom)
        //            if (fun.Name == "neg") return Atom(-asNum(eval(x)))
        //            if (fun.Name == "i") return x
        //            if (fun.Name == "nil") return t
        //            if (fun.Name == "isnil") return Ap(x, Ap(t, Ap(t, f)))
        //            if (fun.Name == "car") return Ap(x, t)
        //            if (fun.Name == "cdr") return Ap(x, f)
        //        if (fun is Ap)
        //            Expr fun2 = eval(fun.Fun)
        //            Expr y = fun.Arg
        //            if (fun2 is Atom)
        //                if (fun2.Name == "t") return y
        //                if (fun2.Name == "f") return x
        //                if (fun2.Name == "add") return Atom(asNum(eval(x)) + asNum(eval(y)))
        //                if (fun2.Name == "mul") return Atom(asNum(eval(x)) * asNum(eval(y)))
        //                if (fun2.Name == "div") return Atom(asNum(eval(y)) / asNum(eval(x)))
        //                if (fun2.Name == "lt") return asNum(eval(y)) < asNum(eval(x)) ? t : f
        //                if (fun2.Name == "eq") return asNum(eval(x)) == asNum(eval(y)) ? t : f
        //                if (fun2.Name == "cons") return evalCons(y, x)
        //            if (fun2 is Ap)
        //                Expr fun3 = eval(fun2.Fun)
        //                Expr z = fun2.Arg
        //                if (fun3 is Atom)
        //                    if (fun3.Name == "s") return Ap(Ap(z, x), Ap(y, x))
        //                    if (fun3.Name == "c") return Ap(Ap(z, x), y)
        //                    if (fun3.Name == "b") return Ap(z, Ap(y, x))
        //                    if (fun3.Name == "cons") return Ap(Ap(x, z), y)
        //    return expr
            }
        }
    }

    Ok(expr.clone())
}

fn print_images(points: ExprRef) {
    panic!("print_images is not yet implemented");
}

fn request_click_from_user() -> Point {
    panic!("request_click_from_user is not yet implemented");
}

fn main() {
    let CONS: ExprRef = Rc::new(RefCell::new(Atom{name: "cons".to_owned()}));
    let T: ExprRef = Rc::new(RefCell::new(Atom{name: "t".to_owned()}));
    let F: ExprRef = Rc::new(RefCell::new(Atom{name: "f".to_owned()}));
    let NIL: ExprRef = Rc::new(RefCell::new(Atom{name: "nil".to_owned()}));

    let functions = parse_functions("DUMMY VALUE");

    // See https://message-from-space.readthedocs.io/en/latest/message39.html
    let mut state: ExprRef = NIL;
    let mut point = Point{ x: 0, y: 0};

    loop {
        let click = Rc::new(RefCell::new(Ap{
            func: Rc::new(RefCell::new(Ap{
                func: CONS.clone(),
                arg: Rc::new(RefCell::new(Atom {name: point.x.to_string(), ..Default::default()})),
                _evaluated: None,
            })),
            arg: Rc::new(RefCell::new(Atom{name: point.y.to_string(), ..Default::default()})),
            _evaluated: None,
        }));
        let (newState, images) = interact(state.clone(), click.clone(), &functions);
        print_images(images);
        point = request_click_from_user();
        state = newState;
    }
// 
// 
// Expr evalCons(Expr a, Expr b)
//     Expr res = Ap(Ap(cons, eval(a)), eval(b))
//     res.Evaluated = res
//     return res
// 
// number asNum(Expr n)
//     if (n is Atom)
//         return PARSE_NUMBER(n.Name)
//     ERROR("not a number")
}

#[cfg(test)]
mod tests {
    #[test]
    fn pseudo_it_works() {
        assert_eq!(2 + 2, 4);
    }
}
