
import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import type { Story } from '../types';
import { ArrowLeft } from 'lucide-react';

const StoryPage: React.FC = () => {
  const location = useLocation();
  const story = location.state?.story as Story | undefined;

  if (!story) {
    return (
      <div className="text-center">
        <h2 className="text-2xl font-bold">No story found!</h2>
        <p className="mt-2">Please go back and create a new story.</p>
        <Link to="/" className="inline-block mt-4 px-6 py-2 text-white bg-purple-600 rounded-full hover:bg-purple-700">
          Create a Story
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <Link to="/" className="inline-flex items-center gap-2 text-purple-600 hover:text-purple-800 mb-6 font-medium">
        <ArrowLeft size={20} />
        Create another story
      </Link>
      <div className="bg-white rounded-2xl shadow-xl overflow-hidden p-4 md:p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
          <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden shadow-inner">
            <img 
              src={story.imageUrl || 'https://picsum.photos/800/800'} 
              alt={story.prompt} 
              className="w-full h-full object-cover" 
            />
          </div>
          <div className="prose lg:prose-xl max-w-none">
            <h1 className="text-3xl md:text-4xl font-bold !mb-2 text-gray-800 capitalize">{story.prompt}</h1>
            <p className="text-gray-500 text-sm">A story woven just for you...</p>
            <div className="mt-6 text-gray-700 leading-relaxed whitespace-pre-wrap">
              {story.text}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StoryPage;
