interface InteractiveQuizProps {
  quizText?: string;
}

const InteractiveQuiz = ({ quizText }: InteractiveQuizProps) => {
  if (!quizText) {
    return (
      <div className="rounded-2xl border border-slate-700 bg-slate-900/50 p-8 text-center text-sm text-slate-300">
        No quiz available yet. Submit a video to generate one.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/50 p-6 sm:p-7">
      <h2 className="mb-4 text-xl font-semibold text-slate-100">Test Your Knowledge</h2>
      <div className="whitespace-pre-wrap text-sm leading-7 text-slate-200 sm:text-[15px]">{quizText}</div>
    </div>
  );
};

export default InteractiveQuiz;