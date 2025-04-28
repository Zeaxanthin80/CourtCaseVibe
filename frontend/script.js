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
            
            // Create statutes summary section
            let statutesSummary = '';
            if (item.statutes && item.statutes.length > 0) {
                // Create comparison results display if available
                let comparisonContent = '';
                if (item.statute_comparisons && item.statute_comparisons.length > 0) {
                    comparisonContent = `
                        <div class="statute-comparisons">
                            <h4>Statute Verification Results:</h4>
                            <div class="comparison-list">
                                ${item.statute_comparisons.map(comp => `
                                    <div class="comparison-item ${comp.is_discrepancy ? 'discrepancy' : 'match'}">
                                        <div class="comparison-header">
                                            <span class="statute-id">${comp.statute_id}</span>
                                            <span class="similarity-score">
                                                Match: ${(comp.similarity_score * 100).toFixed(1)}%
                                                ${comp.is_discrepancy ? 
                                                    '<span class="discrepancy-flag">⚠️ Potential Discrepancy</span>' : 
                                                    '<span class="match-flag">✓ Verified</span>'}
                                            </span>
                                        </div>
                                        <div class="comparison-details">
                                            <div class="comparison-section">
                                                <h5>From Hearing:</h5>
                                                <p class="transcript-text">"${escapeHtml(comp.transcript_text)}"</p>
                                            </div>
                                            <div class="comparison-section">
                                                <h5>From Florida Statutes:</h5>
                                                ${comp.error ? 
                                                    `<p class="error-message">${escapeHtml(comp.error)}</p>` :
                                                    `<p class="statute-title">${escapeHtml(comp.title || '')}</p>
                                                     <p class="statute-text">${escapeHtml(truncateText(comp.statute_text, 200))}</p>`
                                                }
                                                <a href="${comp.url}" target="_blank" class="statute-link">View on Official Florida Statutes Website</a>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }
                
                statutesSummary = `
                    <div class="statutes-summary">
                        <h4>Statute References Found (${item.statutes.length}):</h4>
                        <ul class="statutes-list">
                            ${item.statutes.map(statute => `
                                <li>
                                    <span class="statute-id">${statute.statute_id}</span> - 
                                    <span class="statute-text">"${statute.text}"</span>
                                </li>
                            `).join('')}
                        </ul>
                        ${comparisonContent}
                    </div>
                `;
            } else {
                statutesSummary = `
                    <div class="statutes-summary">
                        <p>No statute references found in this transcription.</p>
                    </div>
                `;
            }
            
            transcriptionDiv.innerHTML = `
                <h3>Transcription for File ID: ${item.file_id.substring(0, 8)}...</h3>
                <p><strong>Hearing Date:</strong> ${item.hearing_date}</p>
                ${statutesSummary}
                <div class="transcription-text">
                    ${item.highlighted_transcription || item.transcription}
                </div>
            `;
            
            // Add event listeners for statute reference hovers
            setTimeout(() => {
                const statuteRefs = transcriptionDiv.querySelectorAll('.statute-reference');
                statuteRefs.forEach(ref => {
                    ref.addEventListener('mouseenter', function() {
                        this.classList.add('hover');
                        const statuteId = this.getAttribute('data-statute-id');
                        const relatedRefs = transcriptionDiv.querySelectorAll(`.statute-reference[data-statute-id="${statuteId}"]`);
                        relatedRefs.forEach(relRef => {
                            if (relRef !== this) {
                                relRef.classList.add('related');
                            }
                        });
                    });
                    
                    ref.addEventListener('mouseleave', function() {
                        this.classList.remove('hover');
                        const statuteId = this.getAttribute('data-statute-id');
                        const relatedRefs = transcriptionDiv.querySelectorAll(`.statute-reference[data-statute-id="${statuteId}"]`);
                        relatedRefs.forEach(relRef => {
                            relRef.classList.remove('related');
                        });
                    });
                    
                    ref.addEventListener('click', function() {
                        const statuteId = this.getAttribute('data-statute-id');
                        fetchAndDisplayStatuteDetails(statuteId, this);
                    });
                });
            }, 100);
            
            transcriptionsContainer.appendChild(transcriptionDiv);
        }
    }
    
    // Helper function to fetch and display statute details in a modal
    async function fetchAndDisplayStatuteDetails(statuteId, element) {
        try {
            // Show loading indicator near the clicked element
            const rect = element.getBoundingClientRect();
            const loadingIndicator = document.createElement('div');
            loadingIndicator.className = 'loading-indicator';
            loadingIndicator.textContent = 'Loading statute...';
            loadingIndicator.style.position = 'absolute';
            loadingIndicator.style.top = `${window.scrollY + rect.bottom + 10}px`;
            loadingIndicator.style.left = `${rect.left}px`;
            document.body.appendChild(loadingIndicator);
            
            // Fetch statute details from the API
            const response = await fetch(`http://localhost:8000/statute/${statuteId}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch statute: ${response.statusText}`);
            }
            
            const statuteData = await response.json();
            
            // Remove loading indicator
            document.body.removeChild(loadingIndicator);
            
            // Create statute details modal
            showStatuteModal(statuteData);
        } catch (error) {
            console.error('Error fetching statute details:', error);
            alert(`Error fetching statute details: ${error.message}`);
        }
    }
    
    // Helper function to display a statute modal
    function showStatuteModal(statuteData) {
        // Create modal container
        const modalContainer = document.createElement('div');
        modalContainer.className = 'statute-modal-container';
        
        // Create modal content
        const modalContent = document.createElement('div');
        modalContent.className = 'statute-modal';
        
        // Format the statute text with better readability
        const statuteText = statuteData.text || 'Statute text not available';
        
        modalContent.innerHTML = `
            <div class="statute-modal-header">
                <h3>${statuteData.title || `Statute ${statuteData.statute_id}`}</h3>
                <button class="close-modal">×</button>
            </div>
            <div class="statute-modal-body">
                <p><strong>Statute ID:</strong> ${statuteData.statute_id}</p>
                <div class="statute-full-text">
                    <h4>Full Text:</h4>
                    <pre>${escapeHtml(statuteText)}</pre>
                </div>
                <p class="statute-source">
                    <a href="${statuteData.url}" target="_blank">View on Official Florida Statutes Website</a>
                </p>
                <p class="statute-cache-info">
                    ${statuteData.cached ? 
                        `<span class="cached-tag">Cached</span> Last updated: ${statuteData.last_updated || 'Unknown'}` : 
                        '<span class="live-tag">Live Data</span>'}
                </p>
            </div>
        `;
        
        // Append modal to container
        modalContainer.appendChild(modalContent);
        
        // Append container to body
        document.body.appendChild(modalContainer);
        
        // Add close functionality
        const closeButton = modalContent.querySelector('.close-modal');
        closeButton.addEventListener('click', function() {
            document.body.removeChild(modalContainer);
        });
        
        // Close when clicking outside the modal
        modalContainer.addEventListener('click', function(e) {
            if (e.target === modalContainer) {
                document.body.removeChild(modalContainer);
            }
        });
    }
    
    // Helper function to escape HTML special characters
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Helper function to truncate text with ellipsis
    function truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
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
