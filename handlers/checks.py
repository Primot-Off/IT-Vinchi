import aiohttp
from urllib.parse import urlparse

languages = [
    "python",
    "javascript",
    "java",
    "c",
    "c++",
    "c#",
    "ruby",
    "go",
    "php",
    "html",
    "css",
    "typescript",
    "swift",
    "kotlin",
    "rust",
    "scala",
    "perl",
    "haskell",
    "lua",
    "elixir",
    "clojure",
    "dart",
    "shell",
    "bash",
    "objective-c",
    "groovy",
    "r",
    "matlab",
    "vba",
    "assembly",
    "fortran",
    "cobol",
    "f#",
    "visual basic",
    "holy c",
    "brainfuck",
    "malbolge",
    "yoptascript",
    "vala",
    "node.js",
    "arduino"
]

async def is_valid_github_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return False
        if parsed.netloc != "github.com":
            return False
        if not parsed.path.strip("/"):
            return False
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                return response.status == 200
    except Exception as e:
        print(f"\033[31m[ERROR] is_valid_github_url: {e}")
        return False
    
async def is_valid_language(language: str) -> bool:
    return language.strip().lower() in languages


async def plural_raz(n: int):
    if 11 <= (n % 100) <= 19:
        return "раз"
    n = n % 10
    if n in [0, 1, 5, 6, 7, 8, 9]:
        return "раз"
    if n in [2, 3, 4]:
        return "раза"
    return "раз"


async def plural_age(n: int):
    if 11 <= (n % 100) <= 19:
        return "лет"
    n = n % 10
    if n == 1:
        return "год"
    return "лет"