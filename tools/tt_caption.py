"""Подпись для TikTok из поста Instagram (docs/landing/insta/posts/NNN.json).

python3 tools/tt_caption.py docs/landing/insta/posts/037-call.json

Из подписи Instagram убирается P.S. с призывом «в директ» и длинный список хэштегов;
вместо них — короткий P.S. под TikTok (призыв в комментарии, там его видит алгоритм)
и 4–5 хэштегов (#ииаватар всегда).
"""
import json
import re
import sys


def tt_caption(post):
    cap = post["caption"]
    tags = re.findall(r"#[\wё]+", cap)
    body = re.sub(r"\n*#[\wё]+(\s+#[\wё]+)*\s*$", "", cap).strip()
    paras = [x.strip() for x in re.split(r"\n\s*\n", body) if x.strip()]
    drop = [x for x in paras if x.startswith("P.S.") or "директ" in x]
    body = "\n\n".join(x for x in paras if x not in drop)
    word = None
    for x in drop:
        word = re.search(r"«([А-ЯЁA-Z]+)»", x) or word
    ps = "P.S. Этот ролик целиком сделала нейросеть — лицо, голос и монтаж."
    if word:
        ps += f" Хотите такое видео для своего блога или бизнеса? Напишите «{word.group(1)}» в комментариях."
    keep = [t for t in tags if t != "#ииаватар"][:3]
    return f"{body}\n\n{ps}\n\n" + " ".join(keep + ["#ииаватар", "#нейросеть"])


if __name__ == "__main__":
    print(tt_caption(json.load(open(sys.argv[1]))))
