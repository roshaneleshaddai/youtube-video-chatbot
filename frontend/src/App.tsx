import {  useState } from 'react';
import type { FormEvent } from 'react';
import axios from 'axios';
import { Youtube, MessageSquare, FileText, HelpCircle, Loader } from 'lucide-react';

import ChatInterface from './components/ChatInterface';
import GeneratedSummary from './components/GeneratedSummary';
import InteractiveQuiz from './components/InteractiveQuiz';

type ActiveTab = 'chat' | 'summary' | 'quiz';

interface VideoData {
  summary?: string;
  quiz?: string;
  video_id?: string;
}

function App() {
  const [videoUrl, setVideoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [videoData, setVideoData] = useState<VideoData | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('chat');

  const handleProcessVideo = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!videoUrl) return;

    setLoading(true);
    setVideoData(null);

    try {
      const response = await axios.post<VideoData>('http://localhost:8000/api/video/process', {
        url: videoUrl,
      });
      setVideoData(response.data);
      setActiveTab('summary');
    } catch (error) {
      console.error('Error processing video:', error);
      alert('Failed to process the video. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto w-full max-w-6xl">
        <header className="mb-8 text-center sm:mb-10">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-400/30 bg-indigo-400/10 px-4 py-1.5 text-xs font-medium uppercase tracking-widest text-indigo-200">
            <Youtube size={14} /> Learning Assistant
          </div>
          <h1 className="bg-gradient-to-r from-indigo-300 via-violet-300 to-cyan-300 bg-clip-text text-4xl font-bold tracking-tight text-transparent sm:text-5xl">
            NeuralStudy UI
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-sm text-slate-300 sm:text-base">
            Multimodal Video Understanding & RAG Knowledge Assistant
          </p>
        </header>

        <form
          onSubmit={handleProcessVideo}
          className="mx-auto mb-8 flex w-full max-w-4xl flex-col gap-3 rounded-2xl border border-slate-700/70 bg-slate-900/70 p-3 shadow-soft backdrop-blur sm:flex-row sm:items-center sm:gap-4"
        >
          <div className="flex flex-1 items-center gap-3 rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3">
            <Youtube className="text-indigo-300" size={18} />
            <input
              type="text"
              className="w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-400 focus:outline-none"
              placeholder="Paste YouTube URL here..."
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
            />
          </div>
          <button
            type="submit"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 px-5 py-3 text-sm font-semibold text-white transition hover:from-indigo-400 hover:to-violet-400 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={loading || !videoUrl}
          >
            {loading ? (
              <>
                <Loader size={18} className="animate-spin" /> Processing...
              </>
            ) : (
              'Analyze Video'
            )}
          </button>
        </form>

        {videoData && (
          <div className="rounded-2xl border border-slate-700/80 bg-slate-900/60 p-4 shadow-soft backdrop-blur sm:p-6">
            <div className="mb-5 grid grid-cols-1 gap-2 sm:grid-cols-3">
              <button
                className={`inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition ${
                  activeTab === 'summary'
                    ? 'border-indigo-400/70 bg-indigo-500/20 text-indigo-100'
                    : 'border-slate-700 bg-slate-900/80 text-slate-200 hover:border-slate-500'
                }`}
                onClick={() => setActiveTab('summary')}
              >
                <FileText size={17} /> Summary
              </button>
              <button
                className={`inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition ${
                  activeTab === 'quiz'
                    ? 'border-indigo-400/70 bg-indigo-500/20 text-indigo-100'
                    : 'border-slate-700 bg-slate-900/80 text-slate-200 hover:border-slate-500'
                }`}
                onClick={() => setActiveTab('quiz')}
              >
                <HelpCircle size={17} /> Quiz
              </button>
              <button
                className={`inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition ${
                  activeTab === 'chat'
                    ? 'border-indigo-400/70 bg-indigo-500/20 text-indigo-100'
                    : 'border-slate-700 bg-slate-900/80 text-slate-200 hover:border-slate-500'
                }`}
                onClick={() => setActiveTab('chat')}
              >
                <MessageSquare size={17} /> Chatbot
              </button>
            </div>

            <div>
              {activeTab === 'summary' && <GeneratedSummary summary={videoData.summary} />}
              {activeTab === 'quiz' && <InteractiveQuiz quizText={videoData.quiz} />}
              {activeTab === 'chat' && <ChatInterface videoId={videoData.video_id} />}
            </div>
          </div>
        )}

        {!videoData && !loading && (
          <div className="mx-auto mt-10 max-w-3xl rounded-2xl border border-slate-700 bg-slate-900/60 p-8 text-center shadow-soft backdrop-blur sm:p-10">
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-500/15 ring-1 ring-indigo-400/30">
              <Youtube size={28} className="text-indigo-300" />
            </div>
            <h3 className="mb-2 text-xl font-semibold text-slate-100">Ready to Learn?</h3>
            <p className="mx-auto max-w-xl text-sm leading-7 text-slate-300 sm:text-base">
              Paste a YouTube URL above. The system will extract audio and visual frames, synthesize a
              Multimodal-Augmented Transcript, generate your study materials, and prepare the RAG chatbot!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;