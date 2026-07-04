from __future__ import annotations

QUIZZES = {
    "SQL Injection": [
        {
            "question": "What makes the vulnerable SQL login unsafe?",
            "options": [
                "It concatenates user input into the query",
                "It hashes passwords",
                "It uses HTTPS",
                "It validates roles",
            ],
            "answer": 0,
        },
        {
            "question": "Why does OR '1'='1' bypass authentication?",
            "options": [
                "It always evaluates to true",
                "It deletes the password",
                "It disables Flask",
                "It encrypts the query",
            ],
            "answer": 0,
        },
        {
            "question": "What does -- usually do in SQL payloads?",
            "options": [
                "Starts a comment",
                "Creates a user",
                "Hashes input",
                "Escapes HTML",
            ],
            "answer": 0,
        },
        {
            "question": "What is the main defense against SQL injection?",
            "options": [
                "Parameterized queries",
                "Longer usernames",
                "Dark mode",
                "Client-side alerts",
            ],
            "answer": 0,
        },
        {
            "question": "Which OWASP category commonly includes injection flaws?",
            "options": [
                "Injection",
                "Cryptographic Failures",
                "Logging only",
                "Broken styling",
            ],
            "answer": 0,
        },
    ],
    "Cross-Site Scripting": [
        {
            "question": "What is rendered by the browser during XSS?",
            "options": ["Injected script or HTML", "SQLite rows", "Password hashes", "Python bytecode"],
            "answer": 0,
        },
        {
            "question": "What is reflected XSS?",
            "options": [
                "Input returned immediately in a response",
                "Input stored in a database only",
                "A password attack",
                "A SQL syntax error",
            ],
            "answer": 0,
        },
        {
            "question": "What is stored XSS?",
            "options": [
                "Malicious input saved and later displayed",
                "A locked account",
                "A prepared statement",
                "A rate limit",
            ],
            "answer": 0,
        },
        {
            "question": "What does HTML escaping do?",
            "options": [
                "Displays markup as text",
                "Executes JavaScript faster",
                "Removes SQL tables",
                "Disables sessions",
            ],
            "answer": 0,
        },
        {
            "question": "Which defense helps reduce XSS impact in browsers?",
            "options": ["Content Security Policy", "Weak passwords", "Unlimited attempts", "Raw HTML output"],
            "answer": 0,
        },
    ],
    "Brute Force": [
        {
            "question": "What enables brute force attacks?",
            "options": ["Repeated guesses", "Escaped HTML", "Prepared SQL", "Static CSS"],
            "answer": 0,
        },
        {
            "question": "Which control slows repeated login attempts?",
            "options": ["Rate limiting", "String concatenation", "Unsafe HTML", "Public passwords"],
            "answer": 0,
        },
        {
            "question": "What does temporary account lockout do?",
            "options": [
                "Blocks more attempts for a short time",
                "Deletes the account",
                "Prints the password",
                "Runs JavaScript",
            ],
            "answer": 0,
        },
        {
            "question": "Why is password hashing important?",
            "options": [
                "It protects stored passwords",
                "It makes brute force unlimited",
                "It disables logging",
                "It creates XSS",
            ],
            "answer": 0,
        },
        {
            "question": "What helps detect brute force behavior?",
            "options": ["Login monitoring", "No logs", "Raw SQL", "Unescaped comments"],
            "answer": 0,
        },
    ],
}


def quiz_for_lab(lab_name: str) -> list[dict]:
    return QUIZZES[lab_name]


def score_quiz(lab_name: str, answers: dict[str, str]) -> int:
    score = 0
    for index, question in enumerate(quiz_for_lab(lab_name)):
        if answers.get(f"q{index}") == str(question["answer"]):
            score += 10
    return score
