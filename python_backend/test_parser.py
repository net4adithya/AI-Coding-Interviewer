import io
import sys
import re
from typing import BinaryIO, Dict, Any

class MockPdfReader:
    class Page:
        def extract_text(self):
            return '''Question Bank — Odd or Even
Question 1: Odd or Even Number
Write a program that reads an integer N and determines whether the number is Odd or Even.
Input:
• A single integer N.
Output:
• Print Even if N is divisible by 2.
• Otherwise, print Odd.
Constraints:
• -10^9 <= N <= 10^9
Example 1:
Input:
8
Output:
Even
Example 2:
Input:
15
Output:
Odd
Expected Concepts:
• Conditional statements
• Modulo (%) operator
• Basic input/output
Difficulty: Easy
Suggested Time: 10 minutes'''
    def __init__(self, _):
        self.pages = [self.Page()]

import sys, types
pypdf = types.ModuleType('pypdf')
pypdf.PdfReader = MockPdfReader
sys.modules['pypdf'] = pypdf

# Now import the parser
sys.path.append('C:\\Users\\admin\\Downloads\\AI Coding Interviewer\\python_backend')
from app.assessment.parsers.pdf_parser import PdfQuestionBankParser

parser = PdfQuestionBankParser()
result = parser.parse(io.BytesIO(b'dummy'))

print('Errors:', result.errors)
print('Num Questions:', len(result.questions))
for i, q in enumerate(result.questions):
    print(f'--- Question {i+1} ---')
    print('Title:', repr(q.title))
    print('Problem Statement:', repr(q.problem_statement))
    print('Difficulty:', q.difficulty)
    print('Topic:', q.topic)
    print('Expected Time:', q.expected_time_minutes)
    print('Examples:', q.examples)
