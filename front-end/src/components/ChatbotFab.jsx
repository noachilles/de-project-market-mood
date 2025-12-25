import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, FileText } from 'lucide-react'; // 아이콘 설치 필요

const ChatbotFab = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', text: '안녕하세요! 투자 관련 궁금한 점을 물어보세요.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // 스크롤 자동 내리기
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userQuestion = input;
    setMessages(prev => [...prev, { role: 'user', text: userQuestion }]);
    setInput('');
    setIsLoading(true);

    try {
      // Django API 호출
      const response = await fetch('/api/chat/ask/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userQuestion }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data = await response.json();
      
      // 봇 응답 및 참고자료(References) 처리
      setMessages(prev => [
        ...prev, 
        { 
          role: 'bot', 
          text: data.answer, 
          references: data.references // 참고 뉴스 함께 저장
        }
      ]);

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'bot', text: '오류가 발생했습니다. 잠시 후 다시 시도해주세요.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* 1. 챗봇 버튼 (우측 상단) */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-5 right-24 z-50 p-3 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all"
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {/* 2. 대화창 모달 */}
      {isOpen && (
        <div className="fixed top-20 right-24 z-50 w-96 h-[500px] bg-white rounded-xl shadow-2xl flex flex-col border border-gray-200 overflow-hidden">
          {/* Header */}
          <div className="bg-blue-600 text-white p-4 font-bold flex justify-between items-center">
            <span>AI Market Analyst</span>
            <span className="text-xs bg-blue-500 px-2 py-1 rounded">RAG Active</span>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 bg-slate-50">
            {messages.map((msg, idx) => (
              <div key={idx} className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-3 rounded-lg text-sm shadow-sm ${
                  msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-br-none' 
                    : 'bg-white text-gray-800 border border-gray-100 rounded-bl-none'
                }`}>
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                  
                  {/* 참고 자료가 있으면 표시 */}
                  {msg.references && msg.references.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-100">
                      <p className="text-xs text-gray-400 font-semibold mb-1 flex items-center gap-1">
                        <FileText size={10} /> 참고 문서
                      </p>
                      <ul className="list-disc pl-3 text-xs text-gray-500 space-y-1">
                        {msg.references.map((ref, i) => (
                          <li key={i} className="line-clamp-1">{ref}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-3 bg-white border-t flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="이번 주 삼성전자 이슈는?"
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
            <button 
              onClick={handleSend}
              disabled={isLoading}
              className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatbotFab;