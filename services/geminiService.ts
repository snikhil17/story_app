
import { GoogleGenAI } from "@google/genai";
import type { UserProfile } from '../types';

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  console.error("API_KEY environment variable not set.");
}

const ai = new GoogleGenAI({ apiKey: API_KEY! });

export const geminiService = {
  generateStory: async (prompt: string, userProfile: UserProfile): Promise<string> => {
    try {
      const fullPrompt = `
        You are a master storyteller for a ${userProfile.age}-year-old ${userProfile.gender === 'Other' ? 'child' : userProfile.gender.toLowerCase()} named ${userProfile.characterName}.
        This child loves ${userProfile.favHobby} and their favorite animal/toy is a ${userProfile.favToyOrAnimal}. Their favorite cartoon character is ${userProfile.favCartoonCharc}.
        They live in ${userProfile.city}, speak ${userProfile.motherTongue}, and their reading level is ${userProfile.readingLevel}.
        
        Based on this, write a short, engaging, and imaginative story about: "${prompt}".

        The story should be positive, age-appropriate, and easy to understand for the child.
        Do not include any introductory or concluding remarks, just provide the story text.
      `;

      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: fullPrompt,
        config: {
          temperature: 0.8,
        }
      });
      return response.text;
    } catch (error) {
      console.error('Error generating story:', error);
      throw new Error('Failed to generate story. Please try again.');
    }
  },

  generateStoryImage: async (prompt: string): Promise<string> => {
    try {
      const imagePrompt = `A whimsical, vibrant children's book illustration style of: "${prompt}". Fantasy, magical, colorful, detailed.`;
      
      const response = await ai.models.generateImages({
        model: 'imagen-4.0-generate-001',
        prompt: imagePrompt,
        config: {
          numberOfImages: 1,
          outputMimeType: 'image/jpeg',
          aspectRatio: '1:1',
        },
      });

      if (response.generatedImages && response.generatedImages.length > 0) {
        const base64ImageBytes = response.generatedImages[0].image.imageBytes;
        return `data:image/jpeg;base64,${base64ImageBytes}`;
      }
      throw new Error('No image was generated.');
    } catch (error) {
      console.error('Error generating image:', error);
      throw new Error('Failed to generate image for the story.');
    }
  },
};
