/** Supported workspace languages and Monaco identifiers. */

export interface WorkspaceLanguage {
  id: string;
  label: string;
  monacoLang: string;
  fileExtension: string;
}

export const WORKSPACE_LANGUAGES: WorkspaceLanguage[] = [
  { id: 'python', label: 'Python 3', monacoLang: 'python', fileExtension: 'py' },
  { id: 'java', label: 'Java', monacoLang: 'java', fileExtension: 'java' },
  { id: 'cpp', label: 'C++', monacoLang: 'cpp', fileExtension: 'cpp' },
  { id: 'javascript', label: 'JavaScript', monacoLang: 'javascript', fileExtension: 'js' },
];

export const DEFAULT_WORKSPACE_LANGUAGE = 'python';

export const STARTER_CODE: Record<string, string> = {
  python: `# Write your solution here
`,
  java: `public class Main {
    public static void main(String[] args) {
        // Write your solution here
    }
}
`,
  cpp: `#include <bits/stdc++.h>
using namespace std;

int main() {
    // Write your solution here
    return 0;
}
`,
  javascript: `const fs = require("fs");

// Write your solution here
`,
};

export function getWorkspaceLanguage(id: string): WorkspaceLanguage | undefined {
  return WORKSPACE_LANGUAGES.find((l) => l.id === id);
}

export function resolveAssessmentLanguage(assessmentLanguage?: string): string {
  const normalized = (assessmentLanguage || DEFAULT_WORKSPACE_LANGUAGE).toLowerCase();
  const match = WORKSPACE_LANGUAGES.find(
    (l) => l.id === normalized || normalized.includes(l.id),
  );
  return match?.id ?? DEFAULT_WORKSPACE_LANGUAGE;
}

export function getStarterCode(language: string): string {
  return STARTER_CODE[language] ?? STARTER_CODE[DEFAULT_WORKSPACE_LANGUAGE];
}
