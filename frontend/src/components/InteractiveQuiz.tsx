import { useState, useMemo, useEffect } from 'react';
import MarkdownRenderer from './MarkdownRenderer';
import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react';

interface InteractiveQuizProps {
  quizText?: string;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
}

interface ParsedQuestion {
  id: number;
  question: string;
  options: { id: string; text: string }[];
  answer: string;
  explanation?: string;
}

function parseQuiz(text: string): ParsedQuestion[] {
  const questions: ParsedQuestion[] = [];
  const lines = text.split('\n');
  let currentQuestion: Partial<ParsedQuestion> | null = null;
  let lastQuestionWasParsed = false;
  
  for (let i = 0; i < lines.length; i++) {
    const origLine = lines[i];
    const trimmed = origLine.replace(/\*\*/g, '').replace(/\*/g, '').trim();
    if (!trimmed) continue;
    
    const qMatch = trimmed.match(/^(\d+)[.)]\s*(.+)/);
    if (qMatch) {
      if (currentQuestion && currentQuestion.question && currentQuestion.options?.length && currentQuestion.answer) {
        questions.push(currentQuestion as ParsedQuestion);
        lastQuestionWasParsed = true;
      }
      currentQuestion = {
        id: parseInt(qMatch[1], 10),
        question: qMatch[2].trim(),
        options: [],
        answer: ''
      };
      lastQuestionWasParsed = false;
      continue;
    }
    
    const optionMatch = trimmed.match(/^([a-d])[.)]\s*(.+)/i);
    const isAnswerLine = trimmed.match(/^(?:Correct\s+)?Answer\s*:?\s*([a-d])/i);
    const explanationMatch = trimmed.match(/^Explanation\s*:?\s*(.+)/i);
    
    if (isAnswerLine && currentQuestion) {
      currentQuestion.answer = isAnswerLine[1].toLowerCase();
      lastQuestionWasParsed = false;
      continue;
    } else if (explanationMatch && currentQuestion) {
      currentQuestion.explanation = explanationMatch[1].trim();
      lastQuestionWasParsed = false;
      continue;
    } else if (optionMatch && currentQuestion) {
      currentQuestion.options!.push({
        id: optionMatch[1].toLowerCase(),
        text: optionMatch[2].trim(),
      });
      lastQuestionWasParsed = false;
      continue;
    }
    
    if (currentQuestion && currentQuestion.options!.length === 0 && !currentQuestion.answer) {
      if (!trimmed.toLowerCase().includes("begin the quiz")) {
        currentQuestion.question += ' ' + trimmed;
      }
      lastQuestionWasParsed = false;
      continue;
    }

    if (currentQuestion && currentQuestion.answer && !currentQuestion.explanation && lastQuestionWasParsed === false) {
      currentQuestion.explanation = trimmed;
    }
  }
  
  if (currentQuestion && currentQuestion.question && currentQuestion.options?.length && currentQuestion.answer) {
    questions.push(currentQuestion as ParsedQuestion);
  }
  
  return questions;
}

const InteractiveQuiz = ({ quizText, onRegenerate, isRegenerating }: InteractiveQuizProps) => {
  const questions = useMemo(() => parseQuiz(quizText || ''), [quizText]);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [isSubmitted, setIsSubmitted] = useState(false);

  // Reset local state if quizText changes
  useEffect(() => {
    setSelectedAnswers({});
    setIsSubmitted(false);
  }, [quizText]);

  if (!quizText && !isRegenerating) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-500">
        No quiz available yet. Submit a video to generate one.
      </div>
    );
  }

  if (isRegenerating) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-sm flex flex-col items-center justify-center">
        <RefreshCw size={28} className="animate-spin text-indigo-500 mb-4" />
        <h3 className="text-lg font-medium text-slate-800">Regenerating Quiz...</h3>
        <p className="text-slate-500 text-sm mt-2">Pondering new questions, this will be quick.</p>
      </div>
    );
  }

  const handleSelect = (qIdx: number, optionId: string) => {
    if (isSubmitted) return;
    setSelectedAnswers(prev => ({ ...prev, [qIdx]: optionId }));
  };

  const calculateScore = () => {
    let score = 0;
    questions.forEach((q, idx) => {
      if (selectedAnswers[idx] === q.answer) score++;
    });
    return score;
  };

  const allAnswered = questions.length > 0 && Object.keys(selectedAnswers).length === questions.length;

  const renderHeader = () => (
    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6">
      <h2 className="text-xl font-semibold text-slate-900">Interactive Quiz</h2>
      <div className="flex items-center gap-3">
        {onRegenerate && (
          <button
            onClick={onRegenerate}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 hover:text-indigo-600 transition-colors"
          >
            <RefreshCw size={14} /> Regenerate
          </button>
        )}
        {isSubmitted && (
          <div className="px-4 py-1.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 font-bold text-sm">
            Score: {calculateScore()} / {questions.length}
          </div>
        )}
      </div>
    </div>
  );

  if (questions.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm">
        {renderHeader()}
        <MarkdownRenderer content={quizText || ''} />
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm">
      {renderHeader()}
      
      <div className="space-y-8">
        {questions.map((q, idx) => {
          const isSelected = selectedAnswers[idx];
          const isAnsweredWrong = isSubmitted && isSelected && isSelected !== q.answer;
          return (
            <div key={idx} className="bg-slate-50 p-5 rounded-xl border border-slate-100">
              <h3 className="text-[15px] font-medium text-slate-800 mb-4 flex gap-2">
                <span className="text-indigo-500 font-bold">{idx + 1}.</span> 
                {q.question}
              </h3>
              <div className="space-y-2">
                {q.options.map((opt) => {
                  const optionIsSelected = selectedAnswers[idx] === opt.id;
                  const isActuallyCorrect = q.answer === opt.id;
                  
                  let optionClass = "flex items-center w-full text-left p-3 rounded-lg border text-sm transition-colors ";
                  
                  if (isSubmitted) {
                    if (isActuallyCorrect) {
                      optionClass += "bg-emerald-50 border-emerald-200 text-emerald-800 font-medium";
                    } else if (optionIsSelected && !isActuallyCorrect) {
                      optionClass += "bg-red-50 border-red-200 text-red-800";
                    } else {
                      optionClass += "bg-white border-slate-200 text-slate-500 opacity-60";
                    }
                  } else {
                    if (optionIsSelected) {
                      optionClass += "bg-indigo-50 border-indigo-300 text-indigo-800 cursor-pointer shadow-sm";
                    } else {
                      optionClass += "bg-white border-slate-200 text-slate-700 hover:border-indigo-300 hover:bg-slate-50 cursor-pointer";
                    }
                  }

                  return (
                    <button
                      key={opt.id}
                      onClick={() => handleSelect(idx, opt.id)}
                      disabled={isSubmitted}
                      className={optionClass}
                    >
                      <span className="w-6 h-6 rounded-md bg-white border shrink-0 flex items-center justify-center text-xs font-bold uppercase mr-3 text-slate-500 shadow-sm">
                        {opt.id}
                      </span>
                      <span>{opt.text}</span>
                      
                      {isSubmitted && isActuallyCorrect && (
                        <CheckCircle2 size={18} className="ml-auto text-emerald-500 shrink-0" />
                      )}
                      {isSubmitted && optionIsSelected && !isActuallyCorrect && (
                        <XCircle size={18} className="ml-auto text-red-500 shrink-0" />
                      )}
                    </button>
                  );
                })}
              </div>

              {isAnsweredWrong && q.explanation && (
                <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                  <div className="font-semibold">Explanation</div>
                  <p className="mt-1 leading-6">{q.explanation}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {!isSubmitted && (
        <div className="mt-8 flex justify-end">
          <button
            onClick={() => setIsSubmitted(true)}
            disabled={!allAnswered}
            className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-sm font-semibold rounded-xl shadow-sm hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Submit Answers
          </button>
        </div>
      )}
      
      {isSubmitted && (
        <div className="mt-8 flex justify-end">
          <button
            onClick={() => {
              setIsSubmitted(false);
              setSelectedAnswers({});
            }}
            className="px-6 py-2.5 bg-white border border-slate-300 text-slate-700 text-sm font-semibold rounded-xl shadow-sm hover:bg-slate-50 transition"
          >
            Retry Quiz
          </button>
        </div>
      )}
    </div>
  );
};

export default InteractiveQuiz;