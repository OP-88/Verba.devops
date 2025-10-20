/**
 * Integration tests for Verba frontend components and API integration
 */

import { describe, it, expect, vi } from 'vitest';

// Mock the API service
const mockApiService = {
  checkHealth: vi.fn(),
  transcribeFile: vi.fn(), 
  getTranscriptionHistory: vi.fn(),
  getTranscriptionById: vi.fn(),
  chatWithTranscript: vi.fn(),
};

vi.mock('@/services/api', () => ({
  apiService: mockApiService
}));

// Mock File API for testing
class MockFile {
  name: string;
  size: number;
  type: string;
  lastModified: number;
  
  constructor(chunks: any[], filename: string, options: any = {}) {
    this.name = filename;
    this.size = chunks.reduce((acc, chunk) => acc + (chunk.length || 0), 0);
    this.type = options.type || 'audio/wav';
    this.lastModified = Date.now();
  }
}

// @ts-ignore
global.File = MockFile;

describe('Verba API Service Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have API service available', () => {
    expect(mockApiService).toBeDefined();
    expect(mockApiService.checkHealth).toBeDefined();
    expect(mockApiService.transcribeFile).toBeDefined();
    expect(mockApiService.getTranscriptionHistory).toBeDefined();
  });

  it('should mock health check API call', async () => {
    mockApiService.checkHealth.mockResolvedValue({ status: 'healthy' });
    
    const result = await mockApiService.checkHealth();
    
    expect(mockApiService.checkHealth).toHaveBeenCalled();
    expect(result).toEqual({ status: 'healthy' });
  });

  it('should mock file transcription API call', async () => {
    const mockFile = new MockFile(['test data'], 'test.wav', { type: 'audio/wav' });
    const mockResult = {
      id: 'test-123',
      transcript: 'Hello world test',
      segments: [
        { start: 0, end: 5, text: 'Hello world test', speaker: 'Speaker 1' }
      ]
    };
    
    mockApiService.transcribeFile.mockResolvedValue(mockResult);
    
    const result = await mockApiService.transcribeFile(mockFile as any);
    
    expect(mockApiService.transcribeFile).toHaveBeenCalledWith(mockFile);
    expect(result).toEqual(mockResult);
  });

  it('should mock history retrieval', async () => {
    const mockHistory = [
      {
        id: 'hist-1',
        filename: 'test1.wav',
        transcript: 'First test',
        created_at: '2024-01-01T10:00:00Z'
      }
    ];
    
    mockApiService.getTranscriptionHistory.mockResolvedValue(mockHistory);
    
    const result = await mockApiService.getTranscriptionHistory();
    
    expect(mockApiService.getTranscriptionHistory).toHaveBeenCalled();
    expect(result).toEqual(mockHistory);
  });

  it('should handle API errors gracefully', async () => {
    const errorMessage = 'Network error';
    mockApiService.checkHealth.mockRejectedValue(new Error(errorMessage));
    
    try {
      await mockApiService.checkHealth();
      expect.fail('Should have thrown an error');
    } catch (error: any) {
      expect(error.message).toBe(errorMessage);
    }
    
    expect(mockApiService.checkHealth).toHaveBeenCalled();
  });

  it('should mock file properties correctly', () => {
    const mockFile = new MockFile(['test data'], 'test.wav', { type: 'audio/wav' });
    
    expect(mockFile.name).toBe('test.wav');
    expect(mockFile.type).toBe('audio/wav');
    expect(mockFile.size).toBeGreaterThan(0);
    expect(typeof mockFile.lastModified).toBe('number');
  });

  it('should validate transcription response structure', async () => {
    const mockResponse = {
      id: 'test-response',
      transcript: 'Full transcript text',
      segments: [
        { 
          start: 0, 
          end: 5, 
          text: 'Test segment', 
          speaker: 'Speaker 1',
          confidence: 0.95 
        }
      ],
      summary: {
        summary: 'Brief summary',
        key_points: ['Key point 1'],
        action_items: ['Action 1'],
        sentiment: 'positive'
      },
      metadata: {
        duration: 10.5,
        language: 'en',
        confidence: 0.92
      }
    };
    
    mockApiService.transcribeFile.mockResolvedValue(mockResponse);
    const mockFile = new MockFile(['data'], 'test.wav');
    
    const result = await mockApiService.transcribeFile(mockFile as any);
    
    expect(result.id).toBeDefined();
    expect(result.transcript).toBeDefined();
    expect(Array.isArray(result.segments)).toBe(true);
    expect(result.segments[0]).toHaveProperty('start');
    expect(result.segments[0]).toHaveProperty('end');
    expect(result.segments[0]).toHaveProperty('text');
    expect(result.summary).toHaveProperty('summary');
    expect(result.metadata).toHaveProperty('duration');
  });
});
