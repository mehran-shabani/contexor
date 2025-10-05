'use client';

import { useState, useEffect } from 'react';
import Textarea from './ui/Textarea';
import Button from './ui/Button';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSave?: () => void;
  readOnly?: boolean;
}

export default function MarkdownEditor({
  value,
  onChange,
  onSave,
  readOnly = false,
}: MarkdownEditorProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [wordCount, setWordCount] = useState(0);

  useEffect(() => {
    // Count words (excluding markdown syntax)
    const text = value
      .replace(/[#*_`\[\]()]/g, '')
      .replace(/\n/g, ' ')
      .trim();
    const words = text.split(/\s+/).filter(word => word.length > 0);
    setWordCount(words.length);
  }, [value]);

  const renderMarkdown = (text: string) => {
    // Simple markdown parser for H2, H3, bold, italic
    let html = text;

    // Headers
    html = html.replace(/^### (.+)$/gm, '<h3 class="text-xl font-semibold mt-4 mb-3 text-gray-700">$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2 class="text-2xl font-bold mt-6 mb-4 text-gray-800">$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1 class="text-3xl font-bold mt-8 mb-4 text-gray-900">$1</h1>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold">$1</strong>');
    html = html.replace(/__(.+?)__/g, '<strong class="font-bold">$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em class="italic">$1</em>');
    html = html.replace(/_(.+?)_/g, '<em class="italic">$1</em>');

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p class="mb-4 leading-relaxed">');
    html = html.replace(/\n/g, '<br>');

    // Wrap in paragraph
    html = '<p class="mb-4 leading-relaxed">' + html + '</p>';

    return html;
  };

  const insertMarkdown = (prefix: string, suffix: string = '') => {
    const textarea = document.getElementById('markdown-textarea') as HTMLTextAreaElement;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end);
    const newText = value.substring(0, start) + prefix + selectedText + suffix + value.substring(end);
    
    onChange(newText);

    // Restore cursor position
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + prefix.length, end + prefix.length);
    }, 0);
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex gap-2">
          {!readOnly && (
            <>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => insertMarkdown('## ', '')}
                title="سرتیتر 2"
              >
                H2
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => insertMarkdown('### ', '')}
                title="سرتیتر 3"
              >
                H3
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => insertMarkdown('**', '**')}
                title="متن ضخیم"
              >
                <strong>B</strong>
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => insertMarkdown('*', '*')}
                title="متن کج"
              >
                <em>I</em>
              </Button>
            </>
          )}
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">
            تعداد کلمات: <strong>{wordCount}</strong>
          </span>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => setShowPreview(!showPreview)}
          >
            {showPreview ? '📝 ویرایش' : '👁 پیش‌نمایش'}
          </Button>
        </div>
      </div>

      {/* Editor / Preview */}
      {showPreview ? (
        <div
          className="markdown-preview border rounded-lg p-6 min-h-[400px] bg-white prose-rtl"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(value) }}
        />
      ) : (
        <Textarea
          id="markdown-textarea"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="font-mono text-sm min-h-[400px]"
          placeholder="محتوای خود را اینجا بنویسید... (از Markdown پشتیبانی می‌شود)"
          readOnly={readOnly}
        />
      )}

      {/* Save Button */}
      {onSave && !readOnly && (
        <div className="flex justify-end">
          <Button onClick={onSave}>
            💾 ذخیره تغییرات
          </Button>
        </div>
      )}
    </div>
  );
}
