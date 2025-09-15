
import type { UserProfile, Story } from '../types';

const USERS_KEY = 'storyweaver_users';
const CURRENT_USER_KEY = 'storyweaver_current_user';
const STORY_HISTORY_KEY_PREFIX = 'storyweaver_story_history_';

class StorageService {
  private getUsers(): Record<string, UserProfile> {
    const users = localStorage.getItem(USERS_KEY);
    return users ? JSON.parse(users) : {};
  }

  getUserProfile(email: string): UserProfile | null {
    const users = this.getUsers();
    return users[email] || null;
  }

  saveUserProfile(profile: UserProfile): void {
    const users = this.getUsers();
    users[profile.email] = profile;
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  }
  
  setCurrentUser(profile: UserProfile): void {
    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify({ email: profile.email }));
  }

  getCurrentUser(): { email: string } | null {
    const user = localStorage.getItem(CURRENT_USER_KEY);
    return user ? JSON.parse(user) : null;
  }

  clearCurrentUser(): void {
    localStorage.removeItem(CURRENT_USER_KEY);
  }

  getStoryHistory(email: string): Story[] {
    const history = localStorage.getItem(`${STORY_HISTORY_KEY_PREFIX}${email}`);
    return history ? JSON.parse(history) : [];
  }

  addStoryToHistory(email: string, story: Story): void {
    const history = this.getStoryHistory(email);
    history.unshift(story); // Add to the beginning
    localStorage.setItem(`${STORY_HISTORY_KEY_PREFIX}${email}`, JSON.stringify(history));
  }
}

export const storageService = new StorageService();
