
import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import type { UserProfile } from '../types';
import { FAV_TOYS_OR_ANIMALS, FAV_HOBBIES, FAV_CARTOON_CHARCS, READING_LEVELS, GENDERS } from '../constants';
import { storageService } from '../services/storageService';

const SignupPage: React.FC = () => {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<Omit<UserProfile, 'email'>>({
    characterName: '',
    gender: 'Other',
    age: 5,
    city: '',
    motherTongue: '',
    favToyOrAnimal: FAV_TOYS_OR_ANIMALS[0],
    favHobby: FAV_HOBBIES[0],
    favCartoonCharc: FAV_CARTOON_CHARCS[0],
    readingLevel: 'Beginner',
  });
  
  const auth = useContext(AuthContext);
  const navigate = useNavigate();

  const handleStep1Submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (storageService.getUserProfile(email)) {
      setError('An account with this email already exists.');
      return;
    }
    setStep(2);
  };
  
  const handleGoogleSignup = () => {
    // Mock Google sign-up
    const mockEmail = `user${Date.now()}@gmail.com`;
    setEmail(mockEmail);
    setPassword('google-signup'); // dummy password
    setStep(2);
  }

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: name === 'age' ? parseInt(value) : value }));
  };

  const handleFinalSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (auth) {
      const fullProfile: UserProfile = { email, ...formData };
      auth.signup(fullProfile);
      navigate('/');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen -m-8">
      <div className="w-full max-w-lg p-8 space-y-6 bg-white rounded-2xl shadow-xl">
        {step === 1 && (
          <>
            <div className="text-center">
              <h1 className="text-4xl font-brand text-purple-600">Join the Magic</h1>
              <p className="text-gray-500 mt-2">Create your account to start an adventure.</p>
            </div>
            {error && <p className="text-red-500 text-sm text-center">{error}</p>}
             <button onClick={handleGoogleSignup} className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google icon" className="w-6 h-6" />
              <span className="font-medium text-gray-700">Sign up with Google</span>
            </button>

            <div className="flex items-center">
              <div className="flex-grow border-t border-gray-300"></div>
              <span className="flex-shrink mx-4 text-gray-500">OR</span>
              <div className="flex-grow border-t border-gray-300"></div>
            </div>

            <form onSubmit={handleStep1Submit} className="space-y-6">
              {/* Form fields identical to login for brevity of example */}
              <div className="relative">
                <input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="block px-4 py-3 w-full text-gray-700 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent peer" placeholder=" " />
                <label htmlFor="email" className="absolute text-gray-500 duration-300 transform -translate-y-4 scale-75 top-3 z-10 origin-[0] bg-white px-2 peer-focus:px-2 peer-focus:text-purple-600 peer-placeholder-shown:scale-100 peer-placeholder-shown:-translate-y-1/2 peer-placeholder-shown:top-1/2 peer-focus:top-3 peer-focus:scale-75 peer-focus:-translate-y-4 left-2">Email Address</label>
              </div>
              <div className="relative">
                <input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="block px-4 py-3 w-full text-gray-700 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent peer" placeholder=" " />
                <label htmlFor="password" className="absolute text-gray-500 duration-300 transform -translate-y-4 scale-75 top-3 z-10 origin-[0] bg-white px-2 peer-focus:px-2 peer-focus:text-purple-600 peer-placeholder-shown:scale-100 peer-placeholder-shown:-translate-y-1/2 peer-placeholder-shown:top-1/2 peer-focus:top-3 peer-focus:scale-75 peer-focus:-translate-y-4 left-2">Password</label>
              </div>
              <button type="submit" className="w-full px-4 py-3 text-white bg-purple-600 rounded-lg hover:bg-purple-700 font-semibold">Continue</button>
            </form>
             <p className="text-center text-sm text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-purple-600 hover:underline">
                Log in
              </Link>
            </p>
          </>
        )}
        {step === 2 && (
          <>
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-800">Tell Us About Your Little Reader</h1>
              <p className="text-gray-500 mt-2">This helps us create the perfect stories!</p>
            </div>
            <form onSubmit={handleFinalSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
              <input type="text" name="characterName" value={formData.characterName} onChange={handleFormChange} placeholder="Child's Name / Character Name" required className="col-span-2 px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500"/>
              
              <select name="gender" value={formData.gender} onChange={handleFormChange} className="px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500">
                {GENDERS.map(g => <option key={g} value={g}>{g}</option>)}
              </select>
              <input type="number" name="age" value={formData.age} onChange={handleFormChange} placeholder="Age" min="1" max="12" required className="px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500"/>
              
              <input type="text" name="city" value={formData.city} onChange={handleFormChange} placeholder="City" required className="px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500"/>
              <input type="text" name="motherTongue" value={formData.motherTongue} onChange={handleFormChange} placeholder="Mother Tongue" required className="px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500"/>

              <select name="favToyOrAnimal" value={formData.favToyOrAnimal} onChange={handleFormChange} className="col-span-2 px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500">
                {FAV_TOYS_OR_ANIMALS.map(item => <option key={item} value={item}>Favorite Toy/Animal: {item}</option>)}
              </select>
              <select name="favHobby" value={formData.favHobby} onChange={handleFormChange} className="col-span-2 px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500">
                {FAV_HOBBIES.map(item => <option key={item} value={item}>Favorite Hobby: {item}</option>)}
              </select>
              <select name="favCartoonCharc" value={formData.favCartoonCharc} onChange={handleFormChange} className="col-span-2 px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500">
                {FAV_CARTOON_CHARCS.map(item => <option key={item} value={item}>Favorite Cartoon: {item}</option>)}
              </select>
               <select name="readingLevel" value={formData.readingLevel} onChange={handleFormChange} className="col-span-2 px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500">
                {READING_LEVELS.map(item => <option key={item} value={item}>Reading Level: {item}</option>)}
              </select>
              <button type="submit" className="col-span-2 w-full px-4 py-3 mt-4 text-white bg-purple-600 rounded-lg hover:bg-purple-700 font-semibold">Create Account & Start Reading</button>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default SignupPage;
