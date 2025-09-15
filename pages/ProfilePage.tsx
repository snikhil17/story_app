
import React, { useState, useContext, useEffect } from 'react';
import { AuthContext } from '../App';
import type { UserProfile } from '../types';
import { FAV_TOYS_OR_ANIMALS, FAV_HOBBIES, FAV_CARTOON_CHARCS, READING_LEVELS, GENDERS } from '../constants';
import { Edit, Save } from 'lucide-react';

const ProfilePage: React.FC = () => {
  const auth = useContext(AuthContext);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<UserProfile | null>(auth?.user || null);
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    setFormData(auth?.user || null);
  }, [auth?.user]);

  if (!formData) {
    return <div>Loading profile...</div>;
  }

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => prev ? { ...prev, [name]: name === 'age' ? parseInt(value) : value } : null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (auth && formData) {
      auth.updateUser(formData);
      setIsEditing(false);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    }
  };

  const renderField = (label: string, name: keyof UserProfile, value: any, type: 'text' | 'number' | 'select', options?: string[]) => {
    return (
      <div className="col-span-2 sm:col-span-1">
        <label htmlFor={name} className="block text-sm font-medium text-gray-700">{label}</label>
        {isEditing ? (
          type === 'select' ? (
            <select
              id={name}
              name={name}
              value={value}
              onChange={handleFormChange}
              className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
            >
              {options?.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </select>
          ) : (
            <input
              type={type}
              id={name}
              name={name}
              value={value}
              onChange={handleFormChange}
              min={type === 'number' ? 1 : undefined}
              max={type === 'number' ? 12 : undefined}
              className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
            />
          )
        ) : (
          <p className="mt-1 text-lg text-gray-900 bg-gray-50 p-2 rounded-md">{value}</p>
        )}
      </div>
    );
  };


  return (
    <div className="max-w-4xl mx-auto">
       <div className="bg-white p-8 rounded-2xl shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Your Profile</h1>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-full hover:bg-purple-700"
          >
            {isEditing ? 'Cancel' : <><Edit size={16}/> Edit Profile</>}
          </button>
        </div>
        
        {showSuccess && (
          <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-6 rounded-md" role="alert">
            <p>Profile updated successfully!</p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-6">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <p className="mt-1 text-lg text-gray-500 bg-gray-50 p-2 rounded-md">{formData.email}</p>
            </div>
            {renderField('Character Name', 'characterName', formData.characterName, 'text')}
            {renderField('Age', 'age', formData.age, 'number')}
            {renderField('Gender', 'gender', formData.gender, 'select', GENDERS)}
            {renderField('City', 'city', formData.city, 'text')}
            {renderField('Mother Tongue', 'motherTongue', formData.motherTongue, 'text')}
            {renderField('Reading Level', 'readingLevel', formData.readingLevel, 'select', READING_LEVELS)}
            {renderField('Favorite Toy/Animal', 'favToyOrAnimal', formData.favToyOrAnimal, 'select', FAV_TOYS_OR_ANIMALS)}
            {renderField('Favorite Hobby', 'favHobby', formData.favHobby, 'select', FAV_HOBBIES)}
            {renderField('Favorite Cartoon', 'favCartoonCharc', formData.favCartoonCharc, 'select', FAV_CARTOON_CHARCS)}
          </div>
          {isEditing && (
            <div className="mt-8 text-right">
              <button
                type="submit"
                className="inline-flex items-center gap-2 justify-center px-6 py-3 border border-transparent text-base font-medium rounded-full shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                <Save size={20}/>
                Save Changes
              </button>
            </div>
          )}
        </form>
       </div>
    </div>
  );
};

export default ProfilePage;
