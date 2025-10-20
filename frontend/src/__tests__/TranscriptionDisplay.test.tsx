import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { toast } from 'sonner';
import { saveAs } from 'file-saver';
import TranscriptionDisplay from '@/components/TranscriptionDisplay';
import { apiService } from '@/services/api';

// Mock dependencies
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock('file-saver', () => ({
  saveAs: jest.fn(),
}));

jest.mock('@/services/api', () => ({
  apiService: {
    baseURL: 'http://localhost:8000',
  },
}));

// Mock fetch
global.fetch = jest.fn();

const mockTranscription = {
  id: 'test-id-123',
  text: 'This is a test transcription with multiple sentences. It contains speaker information and timing data.',
  created_at: '2024-01-01T12:00:00Z',
  duration: 30.5,
  language: 'en',
  confidence: 0.95,
  file_name: 'test-audio.wav',
  segments: [
    {
      start: 0,
      end: 15,
      text: 'This is a test transcription with multiple sentences.',
      speaker: 'Speaker 1',
      confidence: 0.95,
    },
    {
      start: 15,
      end: 30.5,
      text: 'It contains speaker information and timing data.',
      speaker: 'Speaker 2',
      confidence: 0.92,
    },
  ],
  speaker_stats: {
    total_speakers: 2,
    speaker_times: {
      'Speaker 1': 15,
      'Speaker 2': 15.5,
    },
  },
  summary: {
    summary: 'A brief test summary of the transcription content.',
    key_points: ['Test transcription', 'Speaker information', 'Timing data'],
    action_items: ['Review transcription', 'Verify accuracy'],
  },
};

describe('TranscriptionDisplay', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders transcription content correctly', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);

    expect(screen.getByText('test-audio.wav')).toBeInTheDocument();
    expect(screen.getByText('0:30')).toBeInTheDocument(); // Duration
    expect(screen.getByText('95% confidence')).toBeInTheDocument();
    expect(screen.getByText('en')).toBeInTheDocument();
    expect(screen.getByText(mockTranscription.text)).toBeInTheDocument();
  });

  it('displays action buttons correctly', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);

    expect(screen.getByLabelText(/copy transcription/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/edit transcription/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/show export options/i)).toBeInTheDocument();
  });

  it('displays keyboard shortcut hints', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);

    expect(screen.getByText('Ctrl+C: Copy')).toBeInTheDocument();
    expect(screen.getByText('Ctrl+E: Edit')).toBeInTheDocument();
    expect(screen.getByText('Ctrl+S: Export')).toBeInTheDocument();
    expect(screen.getByText('Esc: Cancel')).toBeInTheDocument();
  });

  it('handles copy functionality', async () => {
    const mockWriteText = jest.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText: mockWriteText },
    });

    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    const copyButton = screen.getByLabelText(/copy transcription/i);
    fireEvent.click(copyButton);

    expect(mockWriteText).toHaveBeenCalledWith(mockTranscription.text);
    expect(toast.success).toHaveBeenCalledWith('📋 Transcription copied to clipboard');
  });

  it('toggles edit mode', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    const editButton = screen.getByLabelText(/edit transcription/i);
    fireEvent.click(editButton);

    // Should show textarea in edit mode
    expect(screen.getByPlaceholderText('Edit transcription...')).toBeInTheDocument();
    expect(screen.getByText('Save Changes')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('shows export options when export button is clicked', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    const exportButton = screen.getByLabelText(/show export options/i);
    fireEvent.click(exportButton);

    expect(screen.getByText('Export Options')).toBeInTheDocument();
    expect(screen.getByLabelText(/export as markdown/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/export as pdf/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/export as json/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/export as plain text/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/export as srt/i)).toBeInTheDocument();
  });

  it('handles SRT export locally', async () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    // Open export options
    const exportButton = screen.getByLabelText(/show export options/i);
    fireEvent.click(exportButton);

    // Click SRT export
    const srtButton = screen.getByLabelText(/export as srt/i);
    fireEvent.click(srtButton);

    await waitFor(() => {
      expect(saveAs).toHaveBeenCalled();
      expect(toast.success).toHaveBeenCalledWith('📁 Exported as SRT');
    });
  });

  it('handles backend export formats', async () => {
    // Mock successful fetch response
    const mockBlob = new Blob(['mock content'], { type: 'text/markdown' });
    const mockResponse = {
      ok: true,
      blob: () => Promise.resolve(mockBlob),
      headers: {
        get: jest.fn().mockReturnValue('attachment; filename="test-export.md"'),
      },
    };
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    // Open export options
    const exportButton = screen.getByLabelText(/show export options/i);
    fireEvent.click(exportButton);

    // Click Markdown export
    const markdownButton = screen.getByLabelText(/export as markdown/i);
    fireEvent.click(markdownButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        `http://localhost:8000/export/${mockTranscription.id}?format=markdown&include_metadata=true&include_speaker_labels=true&include_summary=true`
      );
      expect(saveAs).toHaveBeenCalledWith(mockBlob, 'test-export.md');
      expect(toast.success).toHaveBeenCalledWith('📁 Exported as MARKDOWN');
    });
  });

  it('handles export failure with fallback', async () => {
    // Mock failed fetch response
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    // Open export options
    const exportButton = screen.getByLabelText(/show export options/i);
    fireEvent.click(exportButton);

    // Click JSON export
    const jsonButton = screen.getByLabelText(/export as json/i);
    fireEvent.click(jsonButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('❌ Export failed. Please try again.');
      expect(saveAs).toHaveBeenCalled(); // Fallback export
      expect(toast.success).toHaveBeenCalledWith('📁 Exported with basic formatting');
    });
  });

  it('displays segments when available', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);

    expect(screen.getByText('Segments')).toBeInTheDocument();
    expect(screen.getByText('0s - 15s')).toBeInTheDocument();
    expect(screen.getByText('15s - 30s')).toBeInTheDocument();
    expect(screen.getByText('This is a test transcription with multiple sentences.')).toBeInTheDocument();
    expect(screen.getByText('It contains speaker information and timing data.')).toBeInTheDocument();
  });

  it('renders loading state when text is empty', () => {
    const emptyTranscription = { ...mockTranscription, text: '' };
    render(<TranscriptionDisplay transcription={emptyTranscription} />);

    expect(screen.getByText('Processing transcription...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument(); // Loading spinner
  });

  it('formats timestamps correctly', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    // Duration should be formatted as MM:SS
    expect(screen.getByText('0:30')).toBeInTheDocument(); // 30.5 seconds -> 0:30
  });

  it('formats dates correctly', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    // Should format the created date nicely
    expect(screen.getByText(/Jan 1, 2024/)).toBeInTheDocument();
  });

  it('handles edit mode correctly', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    const editButton = screen.getByLabelText(/edit transcription/i);
    fireEvent.click(editButton);

    // Should show textarea with current text
    const textarea = screen.getByDisplayValue(mockTranscription.text);
    expect(textarea).toBeInTheDocument();

    // Change text
    fireEvent.change(textarea, { target: { value: 'Modified transcription text' } });
    expect(textarea).toHaveValue('Modified transcription text');

    // Save changes
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    expect(toast.success).toHaveBeenCalledWith('✏️ Transcription updated');
  });

  it('handles edit cancellation', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    const editButton = screen.getByLabelText(/edit transcription/i);
    fireEvent.click(editButton);

    // Modify text
    const textarea = screen.getByDisplayValue(mockTranscription.text);
    fireEvent.change(textarea, { target: { value: 'Modified text' } });

    // Cancel changes
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    // Should exit edit mode and revert text
    expect(screen.queryByPlaceholderText('Edit transcription...')).not.toBeInTheDocument();
    expect(screen.getByText(mockTranscription.text)).toBeInTheDocument();
  });

  it('shows export loading state', async () => {
    // Mock slow response
    (global.fetch as jest.Mock).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        blob: () => Promise.resolve(new Blob()),
        headers: { get: () => 'test.pdf' }
      }), 100))
    );

    render(<TranscriptionDisplay transcription={mockTranscription} />);
    
    // Open export options
    const exportButton = screen.getByLabelText(/show export options/i);
    fireEvent.click(exportButton);

    // Click PDF export
    const pdfButton = screen.getByLabelText(/export as pdf/i);
    fireEvent.click(pdfButton);

    // Should show loading spinner
    expect(pdfButton).toBeDisabled();
    expect(pdfButton.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('displays accessibility attributes correctly', () => {
    render(<TranscriptionDisplay transcription={mockTranscription} />);

    // Check ARIA labels
    expect(screen.getByLabelText(/copy transcription.*ctrl\+c/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/edit transcription.*ctrl\+e/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/show export options/i)).toBeInTheDocument();

    // Check aria-live region for transcription
    const transcriptionContent = screen.getByText(mockTranscription.text).closest('[aria-live]');
    expect(transcriptionContent).toHaveAttribute('aria-live', 'polite');
  });
});