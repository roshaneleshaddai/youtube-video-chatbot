import { useState } from 'react';
import type { FormEvent } from 'react';
import axios from 'axios';
import { Youtube, MessageSquare, FileText, HelpCircle, Loader, History, FileUp } from 'lucide-react';

import ChatInterface from './components/ChatInterface';
import GeneratedSummary from './components/GeneratedSummary';
import InteractiveQuiz from './components/InteractiveQuiz';

type ActiveTab = 'chat' | 'summary' | 'quiz';
type SourceTab = 'video' | 'document';

interface VideoData {
  summary?: string;
  quiz?: string;
  video_id?: string;
  title?: string;
}

interface HistoryItem {
  sourceType: SourceTab;
  sourceValue: string;
  data: VideoData;
}

function App() {
  const [sourceTab, setSourceTab] = useState<SourceTab>('video');
  const [videoUrl, setVideoUrl] = useState('');
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [videoData, setVideoData] = useState<VideoData | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('chat');
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isRegeneratingQuiz, setIsRegeneratingQuiz] = useState(false);

  const handleProcessVideo = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (sourceTab === 'video' && !videoUrl) return;
    if (sourceTab === 'document' && !documentFile) return;

    setLoading(true);

    try {
      let data: VideoData;

      if (sourceTab === 'video') {
        const response = await axios.post<VideoData>('http://localhost:8000/api/video/process', {
          url: videoUrl,
        });
        data = response.data;
      } else {
        const formData = new FormData();
        formData.append('file', documentFile as File);
        const response = await axios.post<VideoData>('http://localhost:8000/api/document/process', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        data = response.data;
      }

      setVideoData(data);
      setActiveTab('summary');
      
      setHistory(prev => {
        const sourceValue = sourceTab === 'video' ? videoUrl : (documentFile?.name || 'Document');
        const exists = prev.find(
          h => h.data.video_id === data.video_id && h.sourceType === sourceTab && h.sourceValue === sourceValue,
        );
        if (exists) return prev;
        return [{ sourceType: sourceTab, sourceValue, data }, ...prev];
      });
      
    } catch (error) {
      console.error('Error processing source:', error);
      const message = axios.isAxiosError(error)
        ? (error.response?.data?.detail || error.message)
        : 'Unknown error';
      alert(`Failed to process content: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateQuiz = async () => {
    if (sourceTab !== 'video' || !videoUrl || !videoData) return;
    setIsRegeneratingQuiz(true);
    try {
      const response = await axios.post<{quiz: string}>('http://localhost:8000/api/video/regenerate-quiz', {
        url: videoUrl
      });
      
      const newVideoData = { ...videoData, quiz: response.data.quiz };
      setVideoData(newVideoData);
      
      setHistory(prev => prev.map(item => 
        item.data.video_id === newVideoData.video_id ? { ...item, data: newVideoData } : item
      ));
    } catch (error) {
      console.error('Error regenerating quiz:', error);
      alert('Failed to regenerate the quiz.');
    } finally {
      setIsRegeneratingQuiz(false);
    }
  };

  const loadFromHistory = (item: HistoryItem) => {
    setSourceTab(item.sourceType);
    if (item.sourceType === 'video') {
      setVideoUrl(item.sourceValue);
      setDocumentFile(null);
    } else {
      setVideoUrl('');
      setDocumentFile(null);
    }
    setVideoData(item.data);
    setActiveTab('summary');
  };

  // UI layout with sidebar
  return (
    <div className="min-h-screen bg-white">
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 text-center sm:mb-10">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5 text-xs font-medium uppercase tracking-widest text-indigo-700">
            <Youtube size={14} className="text-red-500" /> Learning Assistant
          </div>
          <h1 className="bg-gradient-to-r from-indigo-700 via-violet-700 to-cyan-600 bg-clip-text text-4xl font-bold tracking-tight text-transparent sm:text-5xl">
            VidChat
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-sm text-slate-600 sm:text-base">
            Multimodal Video Understanding & RAG Knowledge Assistant
          </p>
        </header>

        <div className="flex flex-col lg:flex-row gap-6 items-start">
          {/* Main Content Area */}
          <div className="flex-1 w-full flex flex-col items-center">
            <form
              onSubmit={handleProcessVideo}
              className="mb-8 flex w-full max-w-3xl flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-md sm:flex-row sm:items-center sm:gap-4"
            >
              <div className="flex flex-1 flex-col gap-3">
                <div className="grid grid-cols-2 gap-2 rounded-xl border border-slate-200 bg-slate-50 p-1.5">
                  <button
                    type="button"
                    onClick={() => setSourceTab('video')}
                    className={`inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                      sourceTab === 'video'
                        ? 'bg-white text-indigo-700 shadow-sm border border-indigo-200'
                        : 'text-slate-600 hover:bg-white/60'
                    }`}
                  >
                    <Youtube size={16} className="text-red-500" /> Video
                  </button>
                  <button
                    type="button"
                    onClick={() => setSourceTab('document')}
                    className={`inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                      sourceTab === 'document'
                        ? 'bg-white text-indigo-700 shadow-sm border border-indigo-200'
                        : 'text-slate-600 hover:bg-white/60'
                    }`}
                  >
                    <FileUp size={16} className="text-indigo-500" /> Document
                  </button>
                </div>

                {sourceTab === 'video' ? (
                  <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 focus-within:border-indigo-400 focus-within:ring-1 focus-within:ring-indigo-400/50 transition">
                    <Youtube className="text-red-500" size={18} />
                    <input
                      type="text"
                      className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
                      placeholder="Paste YouTube URL here..."
                      value={videoUrl}
                      onChange={(e) => setVideoUrl(e.target.value)}
                    />
                  </div>
                ) : (
                  <label className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 cursor-pointer hover:border-indigo-300 hover:bg-indigo-50/30 transition">
                    <FileUp className="text-indigo-500" size={18} />
                    <span className="truncate">
                      {documentFile ? documentFile.name : 'Upload a document (txt, md, csv, json, log, code files, pdf)'}
                    </span>
                    <input
                      type="file"
                      className="hidden"
                      accept=".txt,.md,.csv,.json,.log,.py,.js,.ts,.pdf"
                      onChange={(e) => {
                        const file = e.target.files?.[0] || null;
                        setDocumentFile(file);
                      }}
                    />
                  </label>
                )}
              </div>
              <button
                type="submit"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-5 py-3 text-sm font-semibold text-white shadow hover:from-indigo-500 hover:to-violet-500 disabled:cursor-not-allowed disabled:opacity-50 transition min-w-[150px]"
                disabled={loading || (sourceTab === 'video' ? !videoUrl : !documentFile)}
              >
                {loading ? (
                  <>
                    <Loader size={18} className="animate-spin" /> Processing...
                  </>
                ) : (
                  sourceTab === 'video' ? 'Analyze Video' : 'Analyze Document'
                )}
              </button>
            </form>

            {videoData && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 shadow-sm sm:p-6 w-full max-w-4xl">
                <div className="mb-5 grid grid-cols-1 gap-2 sm:grid-cols-3">
                  <button
                    className={`inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition ${
                      activeTab === 'summary'
                        ? 'border-indigo-300 bg-indigo-50 text-indigo-700 shadow-sm'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                    onClick={() => setActiveTab('summary')}
                  >
                    <FileText size={17} /> Summary
                  </button>
                  <button
                    className={`inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition ${
                      activeTab === 'quiz'
                        ? 'border-indigo-300 bg-indigo-50 text-indigo-700 shadow-sm'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                    onClick={() => setActiveTab('quiz')}
                  >
                    <HelpCircle size={17} /> Quiz
                  </button>
                  <button
                    className={`inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition ${
                      activeTab === 'chat'
                        ? 'border-indigo-300 bg-indigo-50 text-indigo-700 shadow-sm'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                    onClick={() => setActiveTab('chat')}
                  >
                    <MessageSquare size={17} /> Chatbot
                  </button>
                </div>

                <div>
                  <div className={activeTab === 'summary' ? 'block' : 'hidden'}>
                    <GeneratedSummary summary={videoData.summary} />
                  </div>
                  <div className={activeTab === 'quiz' ? 'block' : 'hidden'}>
                    <InteractiveQuiz 
                      quizText={videoData.quiz} 
                      onRegenerate={sourceTab === 'video' ? handleRegenerateQuiz : undefined}
                      isRegenerating={sourceTab === 'video' ? isRegeneratingQuiz : false}
                    />
                  </div>
                  <div className={activeTab === 'chat' ? 'block' : 'hidden'}>
                    <ChatInterface videoId={videoData.video_id} />
                  </div>
                </div>
              </div>
            )}

            {!videoData && !loading && (
              <div className="mt-10 max-w-3xl rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-10 w-full">
                <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-50 shadow-sm ring-1 ring-indigo-100">
                  <Youtube size={32} className="text-red-500" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-slate-800">Ready to Learn?</h3>
                <p className="mx-auto max-w-xl text-sm leading-7 text-slate-600 sm:text-base">
                  Choose Video to analyze YouTube content or Document to upload study material. The system will
                  generate a summary, quiz, and prepare the RAG chatbot for follow-up questions.
                </p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="w-full lg:w-72 shrink-0">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 shadow-sm sticky top-8">
              <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <History size={18} className="text-indigo-500" /> History
              </h3>
              {history.length === 0 ? (
                <p className="text-sm text-slate-500 py-4 text-center border border-dashed border-slate-300 rounded-lg">
                  No processed content yet.
                </p>
              ) : (
                <ul className="space-y-2 max-h-[600px] overflow-y-auto pretty-scrollbar pr-2">
                  {history.map((item, idx) => {
                    const isActive = videoData?.video_id === item.data.video_id;
                    return (
                      <li key={item.data.video_id || idx}>
                        <button
                          onClick={() => loadFromHistory(item)}
                          className={`w-full text-left p-3 rounded-xl border text-sm transition-colors ${
                            isActive
                              ? 'bg-indigo-50 border-indigo-200 text-indigo-800 shadow-sm'
                              : 'bg-white border-slate-200 text-slate-600 hover:border-indigo-300 hover:bg-slate-50 shadow-sm'
                          }`}
                        >
                          <div className="font-medium truncate mb-1 flex items-center gap-1.5" title={item.data.title}>
                            {item.sourceType === 'video' ? (
                              <Youtube size={14} className={isActive ? "text-indigo-500 shrink-0" : "text-slate-400 shrink-0"} />
                            ) : (
                              <FileUp size={14} className={isActive ? "text-indigo-500 shrink-0" : "text-slate-400 shrink-0"} />
                            )}
                            {item.data.title || `Video ${item.data.video_id?.slice(0, 8)}`}
                          </div>
                          <div className="text-xs text-slate-400 truncate pl-5">
                            {item.sourceType === 'video' ? item.sourceValue : `Document: ${item.sourceValue}`}
                          </div>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;