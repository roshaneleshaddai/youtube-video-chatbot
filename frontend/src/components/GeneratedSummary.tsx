import MarkdownRenderer from './MarkdownRenderer';

interface GeneratedSummaryProps {
  summary?: string;
}

const GeneratedSummary = ({ summary }: GeneratedSummaryProps) => {
  if (!summary) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-500">
        No summary available yet. Submit a video to generate one.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold text-slate-900">Video Summary</h2>
      <MarkdownRenderer content={summary} />
    </div>
  );
};

export default GeneratedSummary;