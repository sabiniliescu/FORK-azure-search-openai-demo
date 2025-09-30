import jsPDF from 'jspdf';

export const exportToPDF = (question: string, answer: string) => {
    const doc = new jsPDF();
    
    // Set font and title
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text('Question & Answer Export', 20, 20);
    
    // Add question section
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Question:', 20, 40);
    
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    
    // Split text for proper line wrapping
    const questionLines = doc.splitTextToSize(question, 170);
    doc.text(questionLines, 20, 50);
    
    // Calculate position for answer section
    const questionHeight = questionLines.length * 7; // Approximate line height
    const answerStartY = 50 + questionHeight + 10;
    
    // Add answer section
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Answer:', 20, answerStartY);
    
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    
    // Clean answer text from HTML tags and citations
    const cleanAnswer = answer
        .replace(/<a [^>]*><sup>\d+<\/sup><\/a>/g, '') // Remove citation links
        .replace(/<[^>]+>/g, '') // Remove all HTML tags
        .replace(/&nbsp;/g, ' ') // Replace HTML entities
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .trim();
    
    const answerLines = doc.splitTextToSize(cleanAnswer, 170);
    doc.text(answerLines, 20, answerStartY + 10);
    
    // Add footer with timestamp
    const now = new Date();
    const timestamp = now.toLocaleString();
    doc.setFontSize(8);
    doc.setFont('helvetica', 'italic');
    doc.text(`Generated on: ${timestamp}`, 20, 280);
    
    // Generate filename with timestamp
    const filename = `QA_Export_${now.toISOString().slice(0, 19).replace(/:/g, '-')}.pdf`;
    
    // Save the PDF
    doc.save(filename);
};