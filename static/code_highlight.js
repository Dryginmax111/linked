/* ============================================================
   code_highlight.js — оффлайн-подсветка синтаксиса.
   Заменяет highlight.js CDN. Не требует интернета.
   Использование: <code class="language-python">...</code>
   Экспортирует window.hljs.highlightElement(el) — совместимо
   с API highlight.js.
   ============================================================ */
(function () {
    if (window.hljs && window.hljs.__reestr) return;

    var KEYWORDS = {
        python: new Set(('and as assert async await break class continue def del elif else ' +
            'except False finally for from global if import in is lambda None nonlocal not ' +
            'or pass raise return True try while with yield print self __init__ __name__').split(/\s+/)),
        sql: new Set(('select from where insert update delete into values set create table ' +
            'alter drop index join left right inner outer full cross on as and or not null ' +
            'is in like between group by order having limit offset distinct union all case ' +
            'when then else end primary key foreign references default constraint unique ' +
            'check if exists count sum avg min max with returning top begin commit rollback ' +
            'grant revoke').split(/\s+/)),
        javascript: new Set(('break case catch class const continue debugger default delete ' +
            'do else export extends finally for function if import in instanceof new return ' +
            'super switch this throw try typeof var void while with yield let async await ' +
            'of from as true false null undefined NaN Infinity').split(/\s+/)),
        typescript: new Set(('interface type enum implements extends public private protected ' +
            'readonly abstract any unknown never string number boolean void null undefined ' +
            'true false as is keyof infer asserts import from export default class function ' +
            'if else for while do switch case break continue return try catch finally throw ' +
            'new this super const let var async await of yield').split(/\s+/)),
        bash: new Set(('if then else elif fi for while until do done case esac function ' +
            'return in exit export local readonly declare echo cd pwd ls mkdir rmdir rm cp ' +
            'mv cat grep sed awk find sort uniq head tail wc chmod chown sudo apt yum dnf ' +
            'pip git docker ps kill top curl wget tar zip unzip').split(/\s+/)),
        json: new Set(['true', 'false', 'null']),
        yaml: new Set(['true', 'false', 'null', 'yes', 'no', 'on', 'off']),
        php: new Set(('function class interface extends implements public private protected ' +
            'static const return if else elseif for foreach while do switch case break ' +
            'continue try catch finally throw new clone instanceof echo print var global ' +
            'isset unset empty array list true false null include require namespace use as').split(/\s+/)),
        ruby: new Set(('def end class module if elsif else unless while until for do then ' +
            'begin rescue ensure raise return yield self nil true false and or not require ' +
            'include attr_accessor puts').split(/\s+/)),
        go: new Set(('package import func var const type struct interface map chan go defer ' +
            'if else for range switch case default break continue return nil true false ' +
            'make new len cap append copy delete panic recover').split(/\s+/)),
        rust: new Set(('fn let mut const static struct enum impl trait for while loop if else ' +
            'match return break continue pub use mod crate self super as where type unsafe ' +
            'true false Some None Ok Err Result Option Vec String').split(/\s+/)),
        java: new Set(('abstract assert boolean break byte case catch char class const continue ' +
            'default do double else enum extends final finally float for goto if implements ' +
            'import instanceof int interface long native new package private protected public ' +
            'return short static strictfp super switch synchronized this throw throws transient ' +
            'try void volatile while true false null').split(/\s+/)),
        c: new Set(('auto break case char const continue default do double else enum extern ' +
            'float for goto if inline int long register restrict return short signed sizeof ' +
            'static struct switch typedef union unsigned void volatile while NULL true false').split(/\s+/)),
        cpp: new Set(('alignas alignof and and_eq asm auto bitand bitor bool break case catch ' +
            'char char16_t char32_t class compl const constexpr const_cast continue decltype ' +
            'default delete do double dynamic_cast else enum explicit export extern false ' +
            'float for friend goto if inline int long mutable namespace new noexcept not ' +
            'nullptr operator or private protected public register reinterpret_cast return ' +
            'short signed sizeof static static_assert static_cast struct switch template this ' +
            'thread_local throw true try typedef typeid typename union unsigned using virtual ' +
            'void volatile wchar_t while').split(/\s+/)),
        csharp: new Set(('abstract as base bool break byte case catch char checked class const ' +
            'continue decimal default delegate do double else enum event explicit extern false ' +
            'finally fixed float for foreach goto if implicit in int interface internal is lock ' +
            'long namespace new null object operator out override params private protected public ' +
            'readonly ref return sbyte sealed short sizeof stackalloc static string struct switch ' +
            'this throw true try typeof uint ulong unchecked unsafe ushort using virtual void ' +
            'volatile while async await var get set').split(/\s+/)),
        css: new Set(('important media supports keyframes import charset font-face and not ' +
            'only or from to').split(/\s+/))
    };

    var LANG_ALIASES = {
        py: 'python', js: 'javascript', ts: 'typescript',
        sh: 'bash', shell: 'bash', zsh: 'bash',
        yml: 'yaml', 'c++': 'cpp', 'c#': 'csharp', cs: 'csharp',
        golang: 'go'
    };

    function normLang(l) {
        if (!l) return '';
        l = String(l).toLowerCase();
        if (LANG_ALIASES[l]) return LANG_ALIASES[l];
        if (l === 'plaintext' || l === 'text' || l === 'txt') return '';
        return l;
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    // Sticky-регексы (флаг y): матчатся строго с lastIndex.
    var RE_STRING = /(?:"""[\s\S]*?"""|'''[\s\S]*?'''|`(?:\\[\s\S]|[^`\\])*`|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')/y;
    var RE_NUMBER = /\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/y;
    var RE_WORD = /[A-Za-z_$@][\w$]*/y;
    var RE_SPACE = /\s+/y;
    var RE_COMMENT_HASH = /#[^\n]*/y;
    var RE_COMMENT_SLASH = /(?:\/\/[^\n]*|\/\*[\s\S]*?\*\/)/y;
    var RE_COMMENT_SQL = /(?:--[^\n]*|\/\*[\s\S]*?\*\/)/y;

    function getCommentRe(lang) {
        if (lang === 'sql') return RE_COMMENT_SQL;
        if (lang === 'python' || lang === 'bash' || lang === 'yaml' || lang === 'ruby') return RE_COMMENT_HASH;
        return RE_COMMENT_SLASH;
    }

    function classifyWord(text, kw) {
        var lower = text.toLowerCase();
        if (kw && kw.has(lower)) return 'keyword';
        if (lower === 'true' || lower === 'false' || lower === 'null' ||
            lower === 'undefined' || lower === 'none' || lower === 'nil') {
            return 'literal';
        }
        return 'ident';
    }

    function highlightToHtml(code, lang) {
        var n = normLang(lang);
        var kw = KEYWORDS[n] || null;
        var reComment = getCommentRe(n);
        var out = [];
        var i = 0;
        var L = code.length;
        while (i < L) {
            var m;
            reComment.lastIndex = i;
            if ((m = reComment.exec(code)) !== null && m.index === i) {
                out.push('<span class="hljs-comment">' + escapeHtml(m[0]) + '</span>');
                i = reComment.lastIndex;
                continue;
            }
            RE_STRING.lastIndex = i;
            if ((m = RE_STRING.exec(code)) !== null && m.index === i) {
                out.push('<span class="hljs-string">' + escapeHtml(m[0]) + '</span>');
                i = RE_STRING.lastIndex;
                continue;
            }
            RE_NUMBER.lastIndex = i;
            if ((m = RE_NUMBER.exec(code)) !== null && m.index === i) {
                out.push('<span class="hljs-number">' + escapeHtml(m[0]) + '</span>');
                i = RE_NUMBER.lastIndex;
                continue;
            }
            RE_WORD.lastIndex = i;
            if ((m = RE_WORD.exec(code)) !== null && m.index === i) {
                var cls = classifyWord(m[0], kw);
                out.push('<span class="hljs-' + cls + '">' + escapeHtml(m[0]) + '</span>');
                i = RE_WORD.lastIndex;
                continue;
            }
            RE_SPACE.lastIndex = i;
            if ((m = RE_SPACE.exec(code)) !== null && m.index === i) {
                out.push(escapeHtml(m[0]));
                i = RE_SPACE.lastIndex;
                continue;
            }
            out.push('<span class="hljs-punct">' + escapeHtml(code[i]) + '</span>');
            i++;
        }
        return out.join('');
    }

    window.hljs = {
        __reestr: true,
        highlightElement: function (el) {
            if (!el) return;
            if (el.dataset && el.dataset.highlighted === '1') return;
            var cls = el.className || '';
            var match = cls.match(/language-([a-zA-Z0-9_+#-]+)/);
            var lang = match ? match[1] : '';
            var code = el.textContent || '';
            try {
                el.innerHTML = highlightToHtml(code, lang);
            } catch (e) {
                /* Ничего не делаем — оставляем как есть */
            }
            el.classList.add('hljs');
            if (el.dataset) el.dataset.highlighted = '1';
        },
        highlightAuto: function (el) {
            window.hljs.highlightElement(el);
        }
    };
})();
