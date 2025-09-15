
export interface UserProfile {
  email: string;
  characterName: string;
  gender: 'Male' | 'Female' | 'Other';
  age: number;
  city: string;
  motherTongue: string;
  favToyOrAnimal: string;
  favHobby: string;
  favCartoonCharc: string;
  readingLevel: 'Beginner' | 'Intermediate' | 'Advanced';
}

export interface Story {
  id: string;
  prompt: string;
  text: string;
  imageUrl: string;
  createdAt: string;
}
