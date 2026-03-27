import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
}

const components: Components = {
  h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mt-6 mb-4 text-slate-900" {...props} />,
  h2: ({ node, ...props }) => <h2 className="text-xl font-bold mt-5 mb-3 text-slate-800" {...props} />,
  h3: ({ node, ...props }) => <h3 className="text-lg font-bold mt-4 mb-2 text-slate-800" {...props} />,
  h4: ({ node, ...props }) => <h4 className="text-base font-bold mt-3 mb-2 text-slate-800" {...props} />,
  h5: ({ node, ...props }) => <h5 className="text-sm font-bold mt-2 mb-1 text-slate-800" {...props} />,
  h6: ({ node, ...props }) => <h6 className="text-xs font-bold mt-2 mb-1 text-slate-800" {...props} />,
  ul: ({ node, ...props }) => <ul className="list-disc pl-6 my-3 space-y-1 text-slate-700" {...props} />,
  ol: ({ node, ...props }) => <ol className="list-decimal pl-6 my-3 space-y-1 text-slate-700" {...props} />,
  li: ({ node, ...props }) => <li className="text-slate-700" {...props} />,
  p: ({ node, ...props }) => <p className="mb-3 text-slate-700 text-sm leading-7 last:mb-0" {...props} />,
  strong: ({ node, ...props }) => <strong className="font-bold text-slate-900" {...props} />,
  em: ({ node, ...props }) => <em className="italic text-slate-800" {...props} />,
  code: ({ node, inline, ...props }: any) => 
    inline 
      ? <code className="bg-slate-100 text-slate-800 px-1 py-0.5 rounded text-sm font-mono" {...props} />
      : <code className="block bg-slate-100 text-slate-800 p-3 rounded-lg text-sm font-mono my-3 overflow-x-auto" {...props} />,
  blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-indigo-400 pl-4 py-1 my-3 bg-slate-50 text-slate-700 italic rounded-r-lg" {...props} />,
};

const MarkdownRenderer = ({ content }: MarkdownRendererProps) => {
  return (
    <div className="markdown-body">
      <ReactMarkdown components={components}>{content}</ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
