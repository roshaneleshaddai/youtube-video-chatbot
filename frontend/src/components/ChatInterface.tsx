import { useState } from 'react';
import axios from 'axios';
import { Send, Loader } from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';

interface ChatInterfaceProps {
  videoId?: string;
}

interface ChatMessage {
  role: 'assistant' | 'user';
  content: string;
}

interface ChatResponse {
  answer: string;
}

const ChatInterface = ({ videoId }: ChatInterfaceProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Hello! Ask me anything about the video.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || !videoId) return;

    const userMessage: ChatMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post<ChatResponse>('http://localhost:8000/api/chat/', {
        video_id: videoId,
        query: userMessage.content,
      });

      setMessages((prev) => [...prev, { role: 'assistant', content: response.data.answer }]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [...prev, { role: 'assistant', content: "Sorry, I couldn't reach the backend." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[560px] flex-col rounded-2xl border border-slate-200 bg-white p-3 sm:p-4 shadow-sm">
      <div className="pretty-scrollbar flex-1 space-y-3 overflow-y-auto rounded-xl border border-slate-100 bg-slate-50 p-3 sm:p-4">
        {messages.map((msg, i) => (
          <div
            key={`${msg.role}-${i}`}
            className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm ${
              msg.role === 'assistant'
                ? 'mr-auto border border-slate-200 bg-white'
                : 'ml-auto bg-gradient-to-r from-indigo-500 to-violet-500 text-white'
            }`}
          >
            <p className={`text-xs font-semibold uppercase tracking-wide ${msg.role === 'assistant' ? 'text-slate-500' : 'text-indigo-100'}`}>
              {msg.role === 'assistant' ? 'Assistant' : 'You'}
            </p>
            <div className={`mt-1 ${msg.role === 'assistant' ? 'text-slate-800' : 'text-white'}`}>
              {msg.role === 'assistant' ? <MarkdownRenderer content={msg.content} /> : <p className="whitespace-pre-wrap text-sm leading-6">{msg.content}</p>}
            </div>
          </div>
        ))}
        {loading && (
          <div className="mr-auto inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 shadow-sm">
            <Loader size={14} className="animate-spin text-indigo-500" /> Thinking...
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center gap-2 rounded-xl border border-slate-200 bg-white p-2 shadow-sm focus-within:border-indigo-400 focus-within:ring-1 focus-within:ring-indigo-400">
        <input
          type="text"
          className="w-full bg-transparent px-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
          placeholder="Ask a question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              void sendMessage();
            }
          }}
        />
        <button
          className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-500 to-violet-500 px-4 py-2 text-sm font-medium text-white transition hover:from-indigo-600 hover:to-violet-600 disabled:cursor-not-allowed disabled:opacity-50"
          onClick={() => void sendMessage()}
          disabled={loading || !videoId}
        >
          <Send size={18} /> Send
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;