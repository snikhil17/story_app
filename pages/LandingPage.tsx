
import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import { geminiService } from '../services/geminiService';
import { storageService } from '../services/storageService';
import type { Story } from '../types';
import Spinner from '../components/Spinner';
import { Sparkles } from 'lucide-react';

const LandingPage: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const auth = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || !auth?.user) return;

    setLoading(true);
    setError('');

    try {
      const [storyText, imageUrl] = await Promise.all([
        geminiService.generateStory(prompt, auth.user),
        geminiService.generateStoryImage(prompt),
      ]);

      const newStory: Story = {
        id: new Date().toISOString(),
        prompt,
        text: storyText,
        imageUrl,
        createdAt: new Date().toISOString(),
      };
      
      storageService.addStoryToHistory(auth.user.email, newStory);
      navigate('/story', { state: { story: newStory } });

    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const storyIdeas = [
    "a friendly dragon who is afraid of heights",
    "a magical treehouse that travels to different worlds",
    "a robot who learns how to bake cookies",
    "an adventure to find a hidden treasure on a pirate ship",
    "a talking squirrel who becomes the king of the forest",
  ];

  const handleIdeaClick = (idea: string) => {
    setPrompt(idea);
  };

  return (
    <div className="max-w-3xl mx-auto text-center">
      <h1 className="text-4xl md:text-5xl font-bold text-gray-800 leading-tight">
        What magical story shall we <span className="font-brand text-purple-600">weave</span> today?
      </h1>
      <p className="mt-4 text-lg text-gray-600">
        Describe a character, a place, or an idea, and we'll bring it to life!
      </p>

      <div className="mt-8">
        <form onSubmit={handleSubmit}>
          <div className="relative">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., A brave knight and a silly dragon on a quest for the perfect pizza"
              className="w-full p-4 pr-12 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-purple-300 focus:border-purple-500 transition-shadow duration-300 resize-none h-28"
              rows={3}
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="mt-4 w-full md:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 text-lg font-semibold text-white bg-purple-600 rounded-full hover:bg-purple-700 disabled:bg-purple-300 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105"
          >
            {loading ? (
              <>
                <Spinner size="sm" color="border-white" />
                Weaving Magic...
              </>
            ) : (
              <>
                <Sparkles size={24} />
                Create Story
              </>
            )}
          </button>
        </form>
        {error && <p className="mt-4 text-red-500">{error}</p>}
      </div>
      
      <div className="mt-12">
        <h3 className="text-xl font-semibold text-gray-700">Need some inspiration?</h3>
        <div className="flex flex-wrap justify-center gap-2 mt-4">
          {storyIdeas.map((idea, index) => (
            <button
              key={index}
              onClick={() => handleIdeaClick(idea)}
              className="px-4 py-2 bg-purple-100 text-purple-700 rounded-full text-sm hover:bg-purple-200 transition-colors"
            >
              {idea}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
