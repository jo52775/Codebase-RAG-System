import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter'
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python'
import oneDark from 'react-syntax-highlighter/dist/esm/styles/prism/one-dark'

SyntaxHighlighter.registerLanguage('python', python)

const mono = '"IBM Plex Mono", ui-monospace, Consolas, monospace'

interface PythonCodeProps {
  code: string
  startingLineNumber?: number
}

export function PythonCode({ code, startingLineNumber }: PythonCodeProps) {
  return (
    <SyntaxHighlighter
      language="python"
      style={oneDark}
      showLineNumbers={startingLineNumber != null}
      startingLineNumber={startingLineNumber}
      customStyle={{
        margin: 0,
        padding: '14px 0',
        background: 'transparent',
        fontSize: '13px',
        lineHeight: 1.6,
        fontFamily: mono,
      }}
      codeTagProps={{
        style: {
          fontFamily: mono,
        },
      }}
      lineNumberStyle={{
        minWidth: '3em',
        paddingRight: '1.1em',
        color: '#6d7484',
        fontStyle: 'normal',
      }}
    >
      {code}
    </SyntaxHighlighter>
  )
}
