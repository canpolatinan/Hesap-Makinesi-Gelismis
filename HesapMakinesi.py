import ast
import json
import math
import operator
import re
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont


class CalcError(Exception):
    pass


NUM, NAME, OP, PCT, FACT, LP, RP = "NUM", "NAME", "OP", "PCT", "FACT", "LP", "RP"

FUNC_NAMES = {
    "sin", "cos", "tan", "asin", "acos", "atan",
    "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
    "log", "ln", "sqrt", "cbrt", "exp", "fact", "abs", "floor", "ceil",
}
CONST_NAMES = {"pi", "e", "ans"}

TOKEN_RE = re.compile(
    r"(?P<num>\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)"
    r"|(?P<name>[A-Za-z_]+)"
    r"|(?P<op>\*\*|//|[-+*/%!])"
    r"|(?P<lp>\()"
    r"|(?P<rp>\))"
)

SYMBOLS = {
    "×": "*", "÷": "/", "−": "-", "–": "-", "—": "-",
    "^": "**", "π": " pi ", "√": " sqrt ", "∛": " cbrt ",
    ",": ".",
}


def _normalize(expression):
    for old, new in SYMBOLS.items():
        expression = expression.replace(old, new)
    return expression


def _tokenize(expression):
    tokens = []
    pos = 0
    while pos < len(expression):
        ch = expression[pos]
        if ch.isspace():
            pos += 1
            continue
        match = TOKEN_RE.match(expression, pos)
        if not match:
            raise CalcError("Geçersiz karakter: '%s'" % ch)
        pos = match.end()

        if match.group("num"):
            raw = match.group("num")
            try:
                if re.fullmatch(r"\d+", raw):
                    value = str(int(raw))
                else:
                    number = float(raw)
                    if math.isinf(number):
                        raise CalcError("Sayı çok büyük")
                    value = repr(number)
            except ValueError:
                raise CalcError("Sayı çok uzun") from None
            tokens.append([NUM, value])
        elif match.group("name"):
            raw = match.group("name")
            name = raw.lower()
            if name == "mod":
                tokens.append([OP, "%"])
            elif name in FUNC_NAMES or name in CONST_NAMES:
                tokens.append([NAME, name])
            else:
                raise CalcError("Bilinmeyen ifade: '%s'" % raw)
        elif match.group("op"):
            op = match.group("op")
            if op == "%":
                tokens.append([PCT, op])
            elif op == "!":
                tokens.append([FACT, op])
            else:
                tokens.append([OP, op])
        elif match.group("lp"):
            tokens.append([LP, "("])
        else:
            tokens.append([RP, ")"])
    return tokens


def to_python(expression):
    tokens = _tokenize(_normalize(expression))

    step1 = []
    i = 0
    while i < len(tokens):
        kind, value = tokens[i]
        step1.append(tokens[i])
        if kind == NAME and value in FUNC_NAMES:
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if nxt is None:
                raise CalcError("'%s' için bir değer girin" % value)
            if nxt[0] != LP:
                if nxt[0] == NUM or (nxt[0] == NAME and nxt[1] in CONST_NAMES):
                    step1 += [[LP, "("], nxt, [RP, ")"]]
                    i += 2
                    continue
                raise CalcError("'%s' için değeri parantez içinde yazın" % value)
        i += 1

    step2 = []
    for token in step1:
        if token[0] not in (PCT, FACT):
            step2.append(token)
            continue
        symbol = "%" if token[0] == PCT else "!"
        if not step2 or step2[-1][0] not in (NUM, RP, NAME) or (
            step2[-1][0] == NAME and step2[-1][1] in FUNC_NAMES
        ):
            raise CalcError("'%s' işaretinden önce bir sayı olmalı" % symbol)
        if step2[-1][0] == RP:
            depth = 0
            j = len(step2) - 1
            while j >= 0:
                if step2[j][0] == RP:
                    depth += 1
                elif step2[j][0] == LP:
                    depth -= 1
                    if depth == 0:
                        break
                j -= 1
            if j < 0:
                raise CalcError("Parantezler uyumsuz")
            start = j
            if j > 0 and step2[j - 1][0] == NAME and step2[j - 1][1] in FUNC_NAMES:
                start = j - 1
        else:
            start = len(step2) - 1
        if token[0] == PCT:
            base = None
            if (start > 0 and step2[start - 1][0] == OP
                    and step2[start - 1][1] in ("+", "-")):
                depth = 0
                g = start - 2
                while g >= 0:
                    if step2[g][0] == RP:
                        depth += 1
                    elif step2[g][0] == LP:
                        if depth == 0:
                            break
                        depth -= 1
                    g -= 1
                base = step2[g + 1:start - 1]
                if (not base or base[-1][0] not in (NUM, RP, NAME)
                        or (base[-1][0] == NAME and base[-1][1] in FUNC_NAMES)):
                    base = None
            operand = step2[start:]
            del step2[start:]
            percent = [[LP, "("]] + operand + [[OP, "/"], [NUM, "100"], [RP, ")"]]
            if base:
                step2 += ([[LP, "("], [LP, "("]] + [t[:] for t in base]
                          + [[RP, ")"], [OP, "*"]] + percent + [[RP, ")"]])
            else:
                step2 += percent
        else:
            step2.insert(start, [NAME, "fact"])
            step2.insert(start + 1, [LP, "("])
            step2.append([RP, ")"])

    final = []
    depth = 0
    for token in step2:
        kind, value = token
        if kind == LP:
            depth += 1
        elif kind == RP:
            depth -= 1
            if depth < 0:
                raise CalcError("Fazladan kapatma parantezi")
        if final:
            prev_kind, prev_value = final[-1]
            prev_is_value = prev_kind in (NUM, RP) or (
                prev_kind == NAME and prev_value in CONST_NAMES
            )
            if prev_is_value and kind in (NUM, LP, NAME):
                final.append([OP, "*"])
        final.append(token)
    final += [[RP, ")"] for _ in range(depth)]

    return " ".join(value for _, value in final)


BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}


class Calculator:
    def __init__(self):
        self.angle_mode = "DEG"
        self.ans = 0

    def _functions(self):
        deg = self.angle_mode == "DEG"

        def to_rad(x):
            return math.radians(x) if deg else x

        def from_rad(x):
            return math.degrees(x) if deg else x

        def clean(value, arg):
            if abs(value) < 1e-14 and abs(arg) > 1e-9:
                return 0.0
            return value

        def sin(x):
            return clean(math.sin(to_rad(x)), x)

        def cos(x):
            return clean(math.cos(to_rad(x)), x)

        def tan(x):
            r = to_rad(x)
            if abs(math.cos(r)) < 1e-14:
                raise CalcError("tan bu açı için tanımsız")
            return clean(math.tan(r), x)

        def asin(x):
            if abs(x) > 1:
                raise CalcError("sin⁻¹ için değer -1 ile 1 arasında olmalı")
            return from_rad(math.asin(x))

        def acos(x):
            if abs(x) > 1:
                raise CalcError("cos⁻¹ için değer -1 ile 1 arasında olmalı")
            return from_rad(math.acos(x))

        def atan(x):
            return from_rad(math.atan(x))

        def acosh(x):
            if x < 1:
                raise CalcError("cosh⁻¹ için değer en az 1 olmalı")
            return math.acosh(x)

        def atanh(x):
            if abs(x) >= 1:
                raise CalcError("tanh⁻¹ için değer -1 ile 1 arasında olmalı")
            return math.atanh(x)

        def log10(x):
            if x <= 0:
                raise CalcError("Logaritma yalnızca pozitif sayılar için tanımlı")
            return math.log10(x)

        def ln(x):
            if x <= 0:
                raise CalcError("Logaritma yalnızca pozitif sayılar için tanımlı")
            return math.log(x)

        def sqrt(x):
            if x < 0:
                raise CalcError("Negatif sayının karekökü gerçek sayı değil")
            return math.sqrt(x)

        def cbrt(x):
            if hasattr(math, "cbrt"):
                return math.cbrt(x)
            return math.copysign(abs(x) ** (1.0 / 3.0), x)

        def fact(x):
            if x != int(x) or x < 0:
                raise CalcError("Faktöriyel yalnızca 0 ve pozitif tam sayılar için")
            if x > 170:
                raise CalcError("Faktöriyel için sayı çok büyük (en fazla 170)")
            return math.factorial(int(x))

        return {
            "sin": sin, "cos": cos, "tan": tan,
            "asin": asin, "acos": acos, "atan": atan,
            "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
            "asinh": math.asinh, "acosh": acosh, "atanh": atanh,
            "log": log10, "ln": ln, "sqrt": sqrt, "cbrt": cbrt,
            "exp": math.exp, "fact": fact, "abs": abs,
            "floor": math.floor, "ceil": math.ceil,
        }

    @staticmethod
    def _power(base, exp):
        if abs(exp) > 1000:
            raise CalcError("Üs çok büyük (en fazla 1000)")
        if base < 0 and exp != int(exp):
            raise CalcError("Negatif sayının kesirli kuvveti gerçek sayı değil")
        if (isinstance(base, int) and isinstance(exp, int)
                and exp > 0 and base.bit_length() * exp > 4096):
            raise OverflowError
        return base ** exp

    def _eval(self, node, funcs):
        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value
            raise CalcError("Desteklenmeyen değer")

        if isinstance(node, ast.BinOp):
            left = self._eval(node.left, funcs)
            right = self._eval(node.right, funcs)
            if isinstance(node.op, ast.Pow):
                return self._power(left, right)
            op = BIN_OPS.get(type(node.op))
            if op is None:
                raise CalcError("Desteklenmeyen işlem")
            return op(left, right)

        if isinstance(node, ast.UnaryOp):
            value = self._eval(node.operand, funcs)
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
            raise CalcError("Desteklenmeyen işlem")

        if isinstance(node, ast.Name):
            if node.id == "pi":
                return math.pi
            if node.id == "e":
                return math.e
            if node.id == "ans":
                return self.ans
            raise CalcError("Bilinmeyen ifade: '%s'" % node.id)

        if isinstance(node, ast.Call):
            if (not isinstance(node.func, ast.Name) or node.func.id not in funcs
                    or node.keywords or len(node.args) != 1):
                raise CalcError("Geçersiz fonksiyon çağrısı")
            return funcs[node.func.id](self._eval(node.args[0], funcs))

        raise CalcError("Desteklenmeyen ifade")

    def evaluate(self, expression, store_ans=True):
        python_expr = to_python(expression)
        try:
            tree = ast.parse(python_expr, mode="eval")
            value = self._eval(tree.body, self._functions())
        except SyntaxError:
            raise CalcError("Sözdizimi hatası") from None
        except ZeroDivisionError:
            raise CalcError("Sıfıra bölme hatası") from None
        except OverflowError:
            raise CalcError("Sayı çok büyük") from None
        except (RecursionError, MemoryError):
            raise CalcError("İfade çok karmaşık") from None
        except ValueError:
            raise CalcError("Geçersiz işlem (tanım kümesi dışında)") from None

        if isinstance(value, complex):
            raise CalcError("Sonuç gerçek sayı değil")
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            raise CalcError("Sonuç tanımsız")
        if store_ans:
            self.ans = value
        return value


def format_number(x):
    if isinstance(x, bool):
        x = int(x)
    if isinstance(x, int):
        if abs(x) < 10 ** 15:
            return str(x)
        try:
            x = float(x)
        except OverflowError:
            raise CalcError("Sayı çok büyük") from None
    if x == 0:
        return "0"
    if x.is_integer() and abs(x) < 1e15:
        return str(int(x))
    text = "%.12g" % x
    return re.sub(r"e([+-])0*(\d)", r"e\1\2", text)


FONT = "Segoe UI"
SETTINGS_PATH = Path.home() / ".gelismis_hesap_makinesi.json"

THEMES = {
    "koyu": {
        "label": "Koyu",
        "bg": "#12141a", "card": "#1c1f28", "border": "#2b3040",
        "fg": "#f5f7fb", "muted": "#8c94a8", "error": "#ff6b6b",
        "accent": "#ff9f0a", "link": "#8fa8ff", "hist_sel": "#33415f",
        "btn": {
            "num":    ("#2b303c", "#ffffff", "#383e4d", "#464d61"),
            "func":   ("#1f232d", "#a9bcff", "#2a2f3c", "#373d4e"),
            "op":     ("#ff9f0a", "#ffffff", "#ffb340", "#e08800"),
            "clear":  ("#e5484d", "#ffffff", "#f06a6f", "#c93a3f"),
            "equals": ("#30c25a", "#ffffff", "#4fd677", "#26a04a"),
            "mem":    ("#191c24", "#8390ad", "#242833", "#2f3441"),
            "mode":   ("#3b4d8c", "#ffffff", "#4a5fa8", "#31417a"),
            "util":   ("#3a404d", "#ffffff", "#4a5162", "#586074"),
        },
    },
    "acik": {
        "label": "Açık",
        "bg": "#eceff5", "card": "#ffffff", "border": "#d9deea",
        "fg": "#1b1e27", "muted": "#7a8195", "error": "#d92d3a",
        "accent": "#ff9500", "link": "#3b53b5", "hist_sel": "#cfd8f5",
        "btn": {
            "num":    ("#ffffff", "#1b1e27", "#f1f3f9", "#dfe4ef"),
            "func":   ("#e2e7f3", "#3b53b5", "#d6ddef", "#c8d1e8"),
            "op":     ("#ff9500", "#ffffff", "#ffab33", "#e08000"),
            "clear":  ("#e5484d", "#ffffff", "#f06a6f", "#c93a3f"),
            "equals": ("#2fb457", "#ffffff", "#47c96e", "#249446"),
            "mem":    ("#e6eaf3", "#6b7390", "#d9dfec", "#cbd3e5"),
            "mode":   ("#3b4d8c", "#ffffff", "#4a5fa8", "#31417a"),
            "util":   ("#d9deec", "#1b1e27", "#cbd2e5", "#bcc5dc"),
        },
    },
}

OPERATOR_CHARS = "+-*/^%×÷−!"
KEY_MAP = {"*": "×", "/": "÷", "-": "−"}


def round_rect(canvas, x1, y1, x2, y2, r, fill, border=None, tags=()):
    def shape(a, b, c, d, rr, color):
        rr = max(0, min(rr, (c - a) / 2, (d - b) / 2))
        dd = 2 * rr
        kw = dict(fill=color, outline=color, tags=tags)
        canvas.create_arc(a, b, a + dd, b + dd, start=90, extent=90, **kw)
        canvas.create_arc(c - dd, b, c, b + dd, start=0, extent=90, **kw)
        canvas.create_arc(c - dd, d - dd, c, d, start=270, extent=90, **kw)
        canvas.create_arc(a, d - dd, a + dd, d, start=180, extent=90, **kw)
        canvas.create_rectangle(a + rr, b, c - rr, d, **kw)
        canvas.create_rectangle(a, b + rr, c, d - rr, **kw)

    if border:
        shape(x1, y1, x2, y2, r, border)
        shape(x1 + 1, y1 + 1, x2 - 1, y2 - 1, r - 1, fill)
    else:
        shape(x1, y1, x2, y2, r, fill)


class RoundButton(tk.Canvas):
    def __init__(self, parent, app, text, command, role="num", size=12,
                 weight="normal", min_w=58, min_h=46, surface="bg"):
        super().__init__(parent, width=app.px(min_w), height=app.px(min_h),
                         highlightthickness=0, bd=0, cursor="hand2", takefocus=0)
        self.app = app
        self.text = text
        self.command = command
        self.role = role
        self.surface = surface
        self.font = (FONT, size, weight)
        self._state = "normal"
        self.configure(bg=app.theme[surface])
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Enter>", lambda e: self._set_state("hover"))
        self.bind("<Leave>", lambda e: self._set_state("normal"))
        self.bind("<ButtonPress-1>", lambda e: self._set_state("pressed"))
        self.bind("<ButtonRelease-1>", self._release)
        app.buttons.append(self)

    def set_text(self, text):
        self.text = text
        self.redraw()

    def _set_state(self, state):
        self._state = state
        self.redraw()

    def _release(self, event):
        inside = (0 <= event.x < self.winfo_width()
                  and 0 <= event.y < self.winfo_height())
        self._set_state("hover" if inside else "normal")
        if inside:
            self.app.run(self.command)

    def redraw(self):
        theme = self.app.theme
        self.configure(bg=theme[self.surface])
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8 or h < 8:
            return
        bg, fg, hover, pressed = theme["btn"][self.role]
        fill = {"normal": bg, "hover": hover, "pressed": pressed}[self._state]
        radius = min(self.app.px(14), (h - 2) // 2, (w - 2) // 2)
        round_rect(self, 0, 0, w, h, radius, fill)
        self.create_text(w / 2, h / 2, text=self.text, fill=fg, font=self.font)


class Card(tk.Canvas):
    def __init__(self, parent, app, height, width=None):
        extra = {"width": width} if width else {}
        super().__init__(parent, height=height, highlightthickness=0, bd=0, **extra)
        self.app = app
        self.inner = tk.Frame(self, bg=app.theme["card"])
        self._win = self.create_window(0, 0, window=self.inner, anchor="nw")
        self.bind("<Configure>", lambda e: self.redraw())

    def redraw(self):
        t = self.app.theme
        self.configure(bg=t["bg"])
        self.inner.configure(bg=t["card"])
        self.delete("card")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20 or h < 20:
            return
        round_rect(self, 0, 0, w, h, self.app.px(18), t["card"],
                   border=t["border"], tags="card")
        self.tag_lower("card")
        pad_x, pad_y = self.app.px(16), self.app.px(8)
        self.coords(self._win, pad_x, pad_y)
        self.itemconfigure(self._win, width=w - 2 * pad_x, height=h - 2 * pad_y)


def _fully_wrapped_negative(text):
    if not (text.startswith("-(") and text.endswith(")")):
        return False
    depth = 0
    for i, ch in enumerate(text[1:], 1):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and i != len(text) - 1:
                return False
    return depth == 0


class CalculatorApp:
    def __init__(self, root, settings_path=SETTINGS_PATH):
        self.root = root
        self.settings_path = settings_path
        self.calc = Calculator()
        self.memory = 0
        self.history = []
        self.just_evaluated = False
        self.history_visible = False
        self.sci_visible = True
        self.theme_name = "koyu"
        self.buttons = []
        self._info_error = False
        self.scale = max(1.0, root.winfo_fpixels("1i") / 96.0)

        self._load_settings()
        self.theme = THEMES[self.theme_name]

        root.title("Gelişmiş Hesap Makinesi v2")
        root.configure(bg=self.theme["bg"])
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.bg_frames = []
        self.main = tk.Frame(root)
        self.main.pack(side="left", fill="both", expand=True)
        self.bg_frames.append(self.main)

        self._build_bar()
        self._build_display()
        self._build_pads()
        self._build_history()

        self.angle_btn.set_text(self.calc.angle_mode)
        self.mode_label.config(text=self.calc.angle_mode)
        self.sci_btn.set_text("Basit mod" if self.sci_visible else "Bilimsel mod")
        self.theme_btn.set_text("Tema: %s" % self.theme["label"])
        if not self.sci_visible:
            self.sci_frame.pack_forget()
            self.basic_frame.pack_configure(padx=0)

        self.apply_theme()
        self._resize()
        self.entry.focus_set()

    def px(self, n):
        return int(round(n * self.scale))

    def run(self, command):
        command()
        self.entry.focus_set()

    def _resize(self):
        self.root.geometry("")
        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_reqwidth(), self.root.winfo_reqheight())

    def _load_settings(self):
        if not self.settings_path:
            return
        try:
            data = json.loads(Path(self.settings_path).read_text(encoding="utf-8"))
            if data.get("theme") in THEMES:
                self.theme_name = data["theme"]
            if data.get("angle") in ("DEG", "RAD"):
                self.calc.angle_mode = data["angle"]
            self.sci_visible = bool(data.get("scientific", True))
            self.history = [(str(a), str(b)) for a, b in data.get("history", [])][:100]
        except Exception:
            pass

    def _save_settings(self):
        if not self.settings_path:
            return
        data = {
            "theme": self.theme_name,
            "angle": self.calc.angle_mode,
            "scientific": self.sci_visible,
            "history": [list(item) for item in self.history[:50]],
        }
        try:
            Path(self.settings_path).write_text(
                json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass

    def on_close(self):
        self._save_settings()
        self.root.destroy()

    def _build_bar(self):
        bar = tk.Frame(self.main)
        bar.pack(fill="x", padx=self.px(12), pady=(self.px(12), 0))
        self.bg_frames.append(bar)

        specs = [
            ("sci_btn", "Bilimsel mod", self.toggle_sci),
            ("hist_btn", "Geçmiş", self.toggle_history),
            ("theme_btn", "Tema", self.toggle_theme),
            ("copy_btn", "Kopyala", self.copy_result),
        ]
        for i, (attr, label, cmd) in enumerate(specs):
            btn = RoundButton(bar, self, label, cmd, "util", size=10,
                            min_w=96, min_h=34)
            btn.grid(row=0, column=i, sticky="ew", padx=self.px(3))
            bar.grid_columnconfigure(i, weight=1, uniform="bar")
            setattr(self, attr, btn)

    def _build_display(self):
        self.card = Card(self.main, self, height=self.px(132))
        self.card.pack(fill="x", padx=self.px(12), pady=(self.px(10), self.px(6)))
        inner = self.card.inner

        top = tk.Frame(inner)
        top.pack(fill="x", pady=(self.px(4), 0))
        self.mode_label = tk.Label(top, text="DEG", font=(FONT, 10, "bold"))
        self.mode_label.pack(side="left")
        self.mem_label = tk.Label(top, text="", font=(FONT, 10, "bold"))
        self.mem_label.pack(side="left", padx=self.px(8))
        self.info_label = tk.Label(top, text="", anchor="e", width=10,
                                   font=(FONT, 12))
        self.info_label.pack(side="left", fill="x", expand=True)

        self.var = tk.StringVar()
        self.entry_font = tkfont.Font(family=FONT, size=34)
        self.entry = tk.Entry(
            inner, textvariable=self.var, font=self.entry_font, justify="right",
            relief="flat", bd=0, highlightthickness=0,
        )
        self.entry.pack(fill="both", expand=True, pady=(0, self.px(4)))

        self.card_widgets = [inner, top, self.mode_label, self.mem_label,
                             self.info_label, self.entry]

        self.entry.bind("<Key>", self.on_key)
        self.entry.bind("<Return>", self.on_return)
        self.entry.bind("<KP_Enter>", self.on_return)
        self.entry.bind("<Escape>", lambda e: (self.clear(), "break")[1])
        self.entry.bind("<Control-c>", self.on_ctrl_c)
        self.entry.bind("<Configure>", self.fit_font)
        self.var.trace_add("write", self._on_change)

    def _btn(self, parent, text, command, role, row, col, span=1,
             size=12, weight="normal"):
        btn = RoundButton(parent, self, text, command, role, size=size,
                          weight=weight)
        btn.grid(row=row, column=col, columnspan=span, sticky="nsew",
                 padx=self.px(3), pady=self.px(3))
        return btn

    def _build_pads(self):
        self.pad = tk.Frame(self.main)
        self.pad.pack(fill="both", expand=True, padx=self.px(8),
                      pady=(0, self.px(12)))
        self.sci_frame = tk.Frame(self.pad)
        self.sci_frame.pack(side="left", fill="both", expand=True)
        self.basic_frame = tk.Frame(self.pad)
        self.basic_frame.pack(side="left", fill="both", expand=True,
                              padx=(self.px(10), 0))
        self.bg_frames += [self.pad, self.sci_frame, self.basic_frame]

        def fn(name):
            return lambda: self.press_function(name)

        def ins(text):
            return lambda: self.insert_text(text)

        sci_rows = [
            [("MC", self.mem_clear, "mem"), ("MR", self.mem_recall, "mem"),
             ("M+", lambda: self.mem_add(1), "mem"),
             ("M−", lambda: self.mem_add(-1), "mem"),
             ("MS", self.mem_store, "mem"), ("DEG", self.toggle_angle, "mode")],
            [("sin", fn("sin("), "func"), ("cos", fn("cos("), "func"),
             ("tan", fn("tan("), "func"), ("sinh", fn("sinh("), "func"),
             ("cosh", fn("cosh("), "func"), ("tanh", fn("tanh("), "func")],
            [("sin⁻¹", fn("asin("), "func"), ("cos⁻¹", fn("acos("), "func"),
             ("tan⁻¹", fn("atan("), "func"), ("sinh⁻¹", fn("asinh("), "func"),
             ("cosh⁻¹", fn("acosh("), "func"), ("tanh⁻¹", fn("atanh("), "func")],
            [("log", fn("log("), "func"), ("ln", fn("ln("), "func"),
             ("10ˣ", fn("10^("), "func"), ("eˣ", fn("exp("), "func"),
             ("√", fn("√("), "func"), ("∛", fn("cbrt("), "func")],
            [("x²", ins("^2"), "func"), ("x³", ins("^3"), "func"),
             ("xʸ", ins("^"), "func"), ("1/x", self.reciprocal, "func"),
             ("n!", ins("!"), "func"), ("|x|", fn("abs("), "func")],
            [("π", ins("π"), "func"), ("e", ins("e"), "func"),
             ("mod", ins(" mod "), "func"), ("floor", fn("floor("), "func"),
             ("ceil", fn("ceil("), "func"), ("EXP", ins("×10^"), "func")],
        ]
        for r, row in enumerate(sci_rows):
            self.sci_frame.grid_rowconfigure(r, weight=1, uniform="r")
            for c, (text, cmd, role) in enumerate(row):
                small = len(text) > 3
                btn = self._btn(self.sci_frame, text, cmd, role,
                                r, c, size=10 if small else 12)
                if text == "DEG":
                    self.angle_btn = btn
        for c in range(6):
            self.sci_frame.grid_columnconfigure(c, weight=1, uniform="c")

        basic_rows = [
            [("C", self.clear, "clear", 1), ("(", ins("("), "util", 1),
             (")", ins(")"), "util", 1), ("⌫", self.backspace, "util", 1)],
            [("±", self.negate, "util", 1), ("%", ins("%"), "util", 1),
             ("Ans", ins("Ans"), "util", 1), ("÷", ins("÷"), "op", 1)],
            [("7", ins("7"), "num", 1), ("8", ins("8"), "num", 1),
             ("9", ins("9"), "num", 1), ("×", ins("×"), "op", 1)],
            [("4", ins("4"), "num", 1), ("5", ins("5"), "num", 1),
             ("6", ins("6"), "num", 1), ("−", ins("−"), "op", 1)],
            [("1", ins("1"), "num", 1), ("2", ins("2"), "num", 1),
             ("3", ins("3"), "num", 1), ("+", ins("+"), "op", 1)],
            [("0", ins("0"), "num", 2), (".", ins("."), "num", 1),
             ("=", self.calculate, "equals", 1)],
        ]
        for r, row in enumerate(basic_rows):
            self.basic_frame.grid_rowconfigure(r, weight=1, uniform="r")
            c = 0
            for text, cmd, role, span in row:
                big = role in ("num", "op", "equals", "clear")
                self._btn(self.basic_frame, text, cmd, role, r, c, span,
                          size=18 if big else 14,
                          weight="bold" if role in ("op", "equals", "clear") else "normal")
                c += span
        for c in range(4):
            self.basic_frame.grid_columnconfigure(c, weight=1, uniform="c")

    def _build_history(self):
        self.history_card = Card(self.root, self, height=self.px(100),
                                 width=self.px(270))
        self.history_frame = self.history_card.inner

        self.hist_title = tk.Label(self.history_frame, text="Geçmiş",
                                   font=(FONT, 14, "bold"))
        self.hist_title.pack(pady=(self.px(12), self.px(6)))

        holder = tk.Frame(self.history_frame)
        holder.pack(fill="both", expand=True, padx=self.px(10))
        scroll = tk.Scrollbar(holder)
        scroll.pack(side="right", fill="y")
        self.hist_list = tk.Listbox(
            holder, bd=0, highlightthickness=0, activestyle="none",
            font=(FONT, 11), yscrollcommand=scroll.set)
        self.hist_list.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.hist_list.yview)
        self.hist_list.bind("<Double-Button-1>", self.use_history)
        for expr, res in self.history:
            self.hist_list.insert(tk.END, "%s = %s" % (expr, res))

        self.hist_hint = tk.Label(self.history_frame, text="Çift tık: sonucu kullan",
                                font=(FONT, 9))
        self.hist_hint.pack(pady=(self.px(4), 0))
        clear_btn = RoundButton(self.history_frame, self, "Geçmişi temizle",
                                self.clear_history, "util", size=11,
                                min_w=100, min_h=36, surface="card")
        clear_btn.pack(fill="x", padx=self.px(10), pady=self.px(10))

        self.hist_widgets = [holder, self.hist_title, self.hist_hint, self.hist_list]

    def apply_theme(self):
        t = self.theme
        self.root.configure(bg=t["bg"])
        for frame in self.bg_frames:
            frame.configure(bg=t["bg"])
        for widget in self.card_widgets:
            widget.configure(bg=t["card"])
        self.entry.configure(fg=t["fg"], insertbackground=t["fg"],
                           selectbackground=t["accent"], selectforeground="#ffffff")
        self.mode_label.configure(fg=t["link"])
        self.mem_label.configure(fg=t["accent"])
        self.info_label.configure(fg=t["error"] if self._info_error else t["muted"])
        self.card.redraw()

        self.history_card.redraw()
        for widget in self.hist_widgets:
            widget.configure(bg=t["card"])
        self.hist_title.configure(fg=t["fg"])
        self.hist_hint.configure(fg=t["muted"])
        self.hist_list.configure(fg=t["fg"], selectbackground=t["hist_sel"],
                                 selectforeground=t["fg"])
        for button in self.buttons:
            button.redraw()

    def toggle_theme(self):
        self.theme_name = "acik" if self.theme_name == "koyu" else "koyu"
        self.theme = THEMES[self.theme_name]
        self.theme_btn.set_text("Tema: %s" % self.theme["label"])
        self.apply_theme()
        self._save_settings()

    def toggle_sci(self):
        if self.sci_visible:
            self.sci_frame.pack_forget()
            self.basic_frame.pack_configure(padx=0)
        else:
            self.sci_frame.pack(side="left", fill="both", expand=True,
                                before=self.basic_frame)
            self.basic_frame.pack_configure(padx=(self.px(10), 0))
        self.sci_visible = not self.sci_visible
        self.sci_btn.set_text("Basit mod" if self.sci_visible else "Bilimsel mod")
        self._resize()
        self._save_settings()

    def toggle_history(self):
        if self.history_visible:
            self.history_card.pack_forget()
        else:
            self.history_card.pack(side="right", fill="y",
                                   padx=(0, self.px(12)), pady=self.px(12))
        self.history_visible = not self.history_visible
        self._resize()

    def set_text(self, text):
        self.var.set(text)
        self.entry.icursor(tk.END)

    def set_info(self, text, error=False):
        self._info_error = error
        self.info_label.config(
            text=text, fg=self.theme["error"] if error else self.theme["muted"])

    def show_error(self, message):
        self.set_info(message, error=True)

    def fit_font(self, *_):
        avail = self.entry.winfo_width() - self.px(16)
        if avail < 40:
            return
        text = self.var.get() or "0"
        size = 34
        while size > 13:
            self.entry_font.configure(size=size)
            if self.entry_font.measure(text) <= avail:
                return
            size -= 2
        self.entry_font.configure(size=12)

    def _on_change(self, *_):
        self.fit_font()
        self.update_preview()

    @staticmethod
    def _is_operator_text(text):
        t = text.strip()
        return t[:1] in OPERATOR_CHARS or t.startswith("mod")

    @staticmethod
    def _value_text(number_text):
        return "(%s)" % number_text if number_text.startswith("-") else number_text

    def on_key(self, event):
        ch = event.char
        if ch in KEY_MAP:
            self.insert_text(KEY_MAP[ch])
            return "break"
        if ch == "=":
            self.calculate()
            return "break"
        if ch and ch.isprintable():
            if self.just_evaluated and ch not in "+^%!":
                self.entry.delete(0, tk.END)
            self.just_evaluated = False
        elif event.keysym in ("BackSpace", "Delete"):
            self.just_evaluated = False
        return None

    def on_return(self, event):
        self.calculate()
        return "break"

    def on_ctrl_c(self, event):
        if self.entry.selection_present():
            return None
        self.copy_result()
        return "break"

    def insert_text(self, text):
        if self.just_evaluated and not self._is_operator_text(text):
            self.entry.delete(0, tk.END)
        self.just_evaluated = False
        if self.entry.selection_present():
            self.entry.delete("sel.first", "sel.last")
        self.entry.insert(self.entry.index(tk.INSERT), text)

    def press_function(self, name):
        current = self.var.get().strip()
        if self.just_evaluated and current:
            self.just_evaluated = False
            self.set_text("%s%s)" % (name, current))
        else:
            self.insert_text(name)

    def reciprocal(self):
        current = self.var.get().strip()
        self.just_evaluated = False
        if current:
            self.set_text("1/(%s)" % current)
        else:
            self.insert_text("1/(")

    def negate(self):
        text = self.var.get().strip()
        self.just_evaluated = False
        if not text:
            self.insert_text("-")
        elif re.fullmatch(r"-?[\d.,]+(e[+-]?\d+)?", text):
            self.set_text(text[1:] if text.startswith("-") else "-" + text)
        elif _fully_wrapped_negative(text):
            self.set_text(text[2:-1])
        else:
            self.set_text("-(%s)" % text)

    def backspace(self):
        self.just_evaluated = False
        if self.entry.selection_present():
            self.entry.delete("sel.first", "sel.last")
        else:
            pos = self.entry.index(tk.INSERT)
            if pos > 0:
                self.entry.delete(pos - 1)

    def clear(self):
        self.just_evaluated = False
        self.var.set("")
        self.set_info("")

    def toggle_angle(self):
        self.calc.angle_mode = "RAD" if self.calc.angle_mode == "DEG" else "DEG"
        self.angle_btn.set_text(self.calc.angle_mode)
        self.mode_label.config(text=self.calc.angle_mode)
        self.update_preview()
        self._save_settings()

    def copy_result(self):
        text = self.var.get().strip()
        if not text:
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
        except tk.TclError:
            return
        previous = (self.info_label.cget("text"), self._info_error)
        self.set_info("Kopyalandı")

        def restore():
            if self.info_label.cget("text") == "Kopyalandı":
                self.set_info(*previous)
        self.root.after(1200, restore)

    def calculate(self):
        if self.just_evaluated:
            return
        text = self.var.get().strip()
        if not text:
            return
        try:
            value = self.calc.evaluate(text)
            result = format_number(value)
        except CalcError as err:
            self.show_error(str(err))
            return
        self.just_evaluated = True
        self.set_text(result)
        self.set_info("%s =" % text)
        self.add_history(text, result)
        self._save_settings()

    def update_preview(self, *_):
        if self.just_evaluated:
            return
        text = self.var.get().strip()
        if not text:
            self.set_info("")
            return
        try:
            preview = format_number(self.calc.evaluate(text, store_ans=False))
        except CalcError:
            self.set_info("")
            return
        self.set_info("" if preview == text else "= %s" % preview)

    def _current_value(self):
        text = self.var.get().strip()
        if not text:
            return None
        try:
            return self.calc.evaluate(text, store_ans=False)
        except CalcError as err:
            self.show_error(str(err))
            return None

    def _update_memory_label(self):
        self.mem_label.config(text="M" if self.memory != 0 else "")
        try:
            self.set_info("Bellek = %s" % format_number(self.memory))
        except CalcError:
            self.set_info("Bellek dolu")

    def mem_clear(self):
        self.memory = 0
        self._update_memory_label()

    def mem_recall(self):
        try:
            text = format_number(self.memory)
        except CalcError as err:
            self.show_error(str(err))
            return
        self.insert_text(self._value_text(text))

    def mem_add(self, sign):
        value = self._current_value()
        if value is None:
            return
        self.memory += sign * value
        self._update_memory_label()

    def mem_store(self):
        value = self._current_value()
        if value is None:
            return
        self.memory = value
        self._update_memory_label()

    def add_history(self, expression, result):
        self.history.insert(0, (expression, result))
        self.hist_list.insert(0, "%s = %s" % (expression, result))
        if len(self.history) > 100:
            self.history.pop()
            self.hist_list.delete(tk.END)

    def use_history(self, event):
        selection = self.hist_list.curselection()
        if not selection:
            return
        _, result = self.history[selection[0]]
        self.insert_text(self._value_text(result))
        self.entry.focus_set()

    def clear_history(self):
        self.history.clear()
        self.hist_list.delete(0, tk.END)
        self._save_settings()


def main():
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    CalculatorApp(root)
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) // 3
    root.geometry("+%d+%d" % (max(x, 0), max(y, 0)))
    root.mainloop()


if __name__ == "__main__":
    main()