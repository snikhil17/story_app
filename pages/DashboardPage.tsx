
import React, { useContext, useMemo } from 'react';
import { AuthContext } from '../App';
import { storageService } from '../services/storageService';
import type { Story } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Book, Clock } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const auth = useContext(AuthContext);
  const storyHistory = useMemo(() => {
    return auth?.user ? storageService.getStoryHistory(auth.user.email) : [];
  }, [auth?.user]);

  const storiesPerDay = useMemo(() => {
    const counts: { [key: string]: number } = {};
    storyHistory.forEach(story => {
      const date = new Date(story.createdAt).toLocaleDateString('en-CA'); // YYYY-MM-DD format
      counts[date] = (counts[date] || 0) + 1;
    });

    return Object.entries(counts)
      .map(([name, stories]) => ({ name, stories }))
      .sort((a, b) => new Date(a.name).getTime() - new Date(b.name).getTime())
      .slice(-10); // show last 10 days of activity
  }, [storyHistory]);
  
  const totalStories = storyHistory.length;
  const lastStoryDate = totalStories > 0 ? new Date(storyHistory[0].createdAt).toLocaleDateString() : 'N/A';

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Parental Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white p-6 rounded-2xl shadow-lg flex items-center gap-6">
          <div className="bg-purple-100 p-4 rounded-full">
            <Book className="text-purple-600" size={32} />
          </div>
          <div>
            <p className="text-gray-500">Total Stories Read</p>
            <p className="text-3xl font-bold text-gray-800">{totalStories}</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-lg flex items-center gap-6">
          <div className="bg-blue-100 p-4 rounded-full">
            <Clock className="text-blue-600" size={32} />
          </div>
          <div>
            <p className="text-gray-500">Last Reading Activity</p>
            <p className="text-3xl font-bold text-gray-800">{lastStoryDate}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-2xl shadow-lg">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Reading Activity (Last 10 Days)</h2>
        {storiesPerDay.length > 0 ? (
          <div style={{ width: '100%', height: 400 }}>
            <ResponsiveContainer>
              <BarChart
                data={storiesPerDay}
                margin={{ top: 5, right: 20, left: -10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip 
                  contentStyle={{
                    background: 'white',
                    border: '1px solid #ccc',
                    borderRadius: '0.5rem'
                  }}
                />
                <Legend />
                <Bar dataKey="stories" fill="#8B5CF6" name="Stories Read" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-center py-16">
            <p className="text-gray-500">No reading activity yet. Create your first story!</p>
          </div>
        )}
      </div>

       <div className="bg-white p-6 mt-8 rounded-2xl shadow-lg">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Recently Read Stories</h2>
         {storyHistory.length > 0 ? (
          <ul className="space-y-3">
            {storyHistory.slice(0, 5).map((story: Story) => (
              <li key={story.id} className="p-3 bg-gray-50 rounded-lg flex justify-between items-center">
                <p className="text-gray-800 font-medium capitalize truncate pr-4">{story.prompt}</p>
                <p className="text-sm text-gray-500 flex-shrink-0">{new Date(story.createdAt).toLocaleDateString()}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-center py-8 text-gray-500">Story history will appear here.</p>
        )}
       </div>
    </div>
  );
};

export default DashboardPage;
