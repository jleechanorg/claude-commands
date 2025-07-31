/**
 * Mock Mode Toggle Component
 *
 * Provides UI for toggling between real and mock API modes.
 * Only visible in development environment.
 */

import React from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { apiWithMock } from '../services/api-with-mock.service';

export function MockModeToggle() {
  const [mockMode, setMockMode] = React.useState(apiWithMock.isMockMode());
  const [currentUser, setCurrentUser] = React.useState('test-user-basic');
  const [errorRate, setErrorRate] = React.useState(0);

  // Only show in development
  if ((import.meta.env as any).PROD) {
    return null;
  }

  const toggleMockMode = () => {
    const newMode = !mockMode;
    apiWithMock.setMockMode(newMode, currentUser);
    setMockMode(newMode);

    // Reload to reinitialize stores
    window.location.reload();
  };

  const switchUser = (userId: string) => {
    setCurrentUser(userId);
    apiWithMock.switchMockUser(userId);

    // Reload to get new user's data
    window.location.reload();
  };

  const updateErrorRate = (rate: number) => {
    setErrorRate(rate);
    apiWithMock.setErrorRate(rate);
  };

  const resetData = () => {
    apiWithMock.resetMockData();
    window.location.reload();
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex items-center gap-2">
      {mockMode && (
        <Badge variant="secondary" className="bg-purple-600 text-white">
          Mock Mode: {currentUser}
        </Badge>
      )}

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="bg-white/90 backdrop-blur"
          >
            🎭 Dev Tools
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-56">
          <DropdownMenuLabel>Mock Mode Settings</DropdownMenuLabel>
          <DropdownMenuSeparator />

          <DropdownMenuItem onClick={toggleMockMode}>
            {mockMode ? '❌ Disable' : '✅ Enable'} Mock Mode
          </DropdownMenuItem>

          {mockMode && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Switch User</DropdownMenuLabel>

              <DropdownMenuItem onClick={() => switchUser('test-user-basic')}>
                👤 Basic User (Adventurer)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => switchUser('test-user-pro')}>
                ⭐ Pro User (Hero)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => switchUser('test-user-gm')}>
                👑 Game Master
              </DropdownMenuItem>

              <DropdownMenuSeparator />
              <DropdownMenuLabel>Error Testing</DropdownMenuLabel>

              <DropdownMenuItem onClick={() => updateErrorRate(0)}>
                ✅ No Errors (0%)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => updateErrorRate(10)}>
                ⚠️ 10% Error Rate
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => updateErrorRate(50)}>
                🔥 50% Error Rate
              </DropdownMenuItem>

              <DropdownMenuSeparator />

              <DropdownMenuItem onClick={resetData}>
                🔄 Reset Mock Data
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
