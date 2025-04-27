document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const uploadForm = document.getElementById('upload-form');
    const hearingDateInput = document.getElementById('hearing-date');
    const addFileBtn = document.getElementById('add-file-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const filesContainer = document.querySelector('.files-container');
    const uploadProgress = document.getElementById('upload-progress');
    const progressBar = uploadProgress.querySelector('.progress');
    const resultsSection = document.getElementById('results-section');
    const transcriptionsContainer = document.getElementById('transcriptions-container');
    const newUploadBtn = document.getElementById('new-upload-btn');

    // Set default hearing date to today
    const today = new Date().toISOString().split('T')[0];
    hearingDateInput.value = today;

    // Add file input
    addFileBtn.addEventListener('click', function() {
        const fileInputDiv = document.createElement('div');
        fileInputDiv.className = 'file-input';
        fileInputDiv.innerHTML = `
            <label for="audio-file">Audio File:</label>
            <input type="file" class="audio-file" name="audio-file" accept=".mp3,.wav,.m4a,.ogg" required>
            <button type="button" class="remove-file-btn">Remove</button>
        `;
        
        // Add event listener to remove button
        const removeBtn = fileInputDiv.querySelector('.remove-file-btn');
        removeBtn.addEventListener('click', function() {
            filesContainer.removeChild(fileInputDiv);
        });
        
        filesContainer.appendChild(fileInputDiv);
    });

    // Show first remove button if there's more than one file input
    document.addEventListener('click', function() {
        const fileInputs = document.querySelectorAll('.file-input');
        if (fileInputs.length > 1) {
            document.querySelectorAll('.remove-file-btn').forEach(btn => {
                btn.style.display = 'inline-block';
            });
        } else {
            document.querySelector('.remove-file-btn').style.display = 'none';
        }
    });

    // Handle form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const hearingDate = hearingDateInput.value;
        const fileInputs = document.querySelectorAll('.audio-file');
        
        if (!hearingDate) {
            alert('Please select a hearing date');
            return;
        }
        
        let hasFiles = false;
        for (const input of fileInputs) {
            if (input.files.length > 0) {
                hasFiles = true;
                break;
            }
        }
        
        if (!hasFiles) {
            alert('Please select at least one audio file');
            return;
        }
        
        // Show progress bar
        uploadBtn.disabled = true;
        uploadProgress.style.display = 'block';
        progressBar.style.width = '0%';
        
        // Upload files and collect file IDs
        const fileIds = [];
        let filesProcessed = 0;
        
        for (const input of fileInputs) {
            if (input.files.length === 0) continue;
            
            const file = input.files[0];
            const formData = new FormData();
            formData.append('file', file);
            formData.append('hearing_date', hearingDate);
            
            try {
                const response = await fetch('http://localhost:8000/upload/', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`Upload failed: ${response.statusText}`);
                }
                
                const data = await response.json();
                fileIds.push(data.file_id);
                
                // Update progress
                filesProcessed++;
                const progress = Math.round((filesProcessed / fileInputs.length) * 50); // First 50% for uploads
                progressBar.style.width = `${progress}%`;
                
            } catch (error) {
                console.error('Error uploading file:', error);
                alert(`Error uploading file: ${error.message}`);
                uploadBtn.disabled = false;
                uploadProgress.style.display = 'none';
                return;
            }
        }
        
        // Transcribe audio files
        try {
            progressBar.style.width = '50%'; // Start second half of progress (transcription)
            
            const transcribeResponse = await fetch('http://localhost:8000/transcribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    hearing_date: hearingDate,
                    file_ids: fileIds
                })
            });
            
            if (!transcribeResponse.ok) {
                throw new Error(`Transcription failed: ${transcribeResponse.statusText}`);
            }
            
            const transcriptions = await transcribeResponse.json();
            
            // Update progress to 100%
            progressBar.style.width = '100%';
            
            // Display transcription results
            displayTranscriptions(transcriptions);
            
            // Hide upload form and show results
            document.getElementById('upload-section').style.display = 'none';
            resultsSection.style.display = 'block';
            
        } catch (error) {
            console.error('Error transcribing audio:', error);
            alert(`Error transcribing audio: ${error.message}`);
        } finally {
            uploadBtn.disabled = false;
            uploadProgress.style.display = 'none';
        }
    });
    
    // Display transcriptions
    function displayTranscriptions(transcriptions) {
        transcriptionsContainer.innerHTML = '';
        
        if (transcriptions.length === 0) {
            transcriptionsContainer.innerHTML = '<p>No transcriptions found.</p>';
            return;
        }
        
        for (const item of transcriptions) {
            const transcriptionDiv = document.createElement('div');
            transcriptionDiv.className = 'transcription-item';
            
            transcriptionDiv.innerHTML = `
                <h3>Transcription for File ID: ${item.file_id.substring(0, 8)}...</h3>
                <p><strong>Hearing Date:</strong> ${item.hearing_date}</p>
                <div class="transcription-text">
                    <p>${item.transcription}</p>
                </div>
            `;
            
            transcriptionsContainer.appendChild(transcriptionDiv);
        }
    }
    
    // New upload button
    newUploadBtn.addEventListener('click', function() {
        // Reset form
        uploadForm.reset();
        hearingDateInput.value = today;
        
        // Remove extra file inputs
        const fileInputs = document.querySelectorAll('.file-input');
        for (let i = 1; i < fileInputs.length; i++) {
            filesContainer.removeChild(fileInputs[i]);
        }
        
        // Hide results and show upload form
        resultsSection.style.display = 'none';
        document.getElementById('upload-section').style.display = 'block';
    });
});
