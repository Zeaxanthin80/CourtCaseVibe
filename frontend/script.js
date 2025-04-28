document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const uploadForm = document.getElementById('upload-form');
    const hearingsContainer = document.getElementById('hearings-container');
    const addHearingBtn = document.getElementById('add-hearing-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadProgress = document.getElementById('upload-progress');
    const progressBar = uploadProgress.querySelector('.progress');
    const resultsSection = document.getElementById('results-section');
    const transcriptionsContainer = document.getElementById('transcriptions-container');
    const newUploadBtn = document.getElementById('new-upload-btn');
    const downloadReportBtn = document.getElementById('download-report-btn');
    
    // Set default hearing date to today for the first hearing
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('hearing-date-1').value = today;

    // Counter for hearings
    let hearingCounter = 1;

    // Add event listeners to the initial file and hearing buttons
    addInitialEventListeners();

    // Add hearing group
    addHearingBtn.addEventListener('click', function() {
        hearingCounter++;
        
        const hearingGroup = document.createElement('div');
        hearingGroup.className = 'hearing-group';
        hearingGroup.innerHTML = `
            <div class="hearing-header">
                <h3>Hearing #${hearingCounter}</h3>
                <button type="button" class="remove-hearing-btn">Remove Hearing</button>
            </div>
            <div class="form-group">
                <label for="hearing-date-${hearingCounter}">Hearing Date:</label>
                <input type="date" class="hearing-date" id="hearing-date-${hearingCounter}" name="hearing-date-${hearingCounter}" required value="${today}">
            </div>
            
            <div class="files-container">
                <div class="file-input">
                    <label for="audio-file-${hearingCounter}-1">Audio File:</label>
                    <input type="file" class="audio-file" id="audio-file-${hearingCounter}-1" name="audio-file-${hearingCounter}-1" accept=".mp3,.wav,.m4a,.ogg" required>
                    <button type="button" class="remove-file-btn" style="display:none;">Remove</button>
                </div>
            </div>

            <button type="button" class="add-file-btn">+ Add Another Audio Part for this Same Hearing Date</button>
        `;
        
        hearingsContainer.appendChild(hearingGroup);
        
        // Add event listeners to the new hearing group
        const newHearing = hearingsContainer.lastElementChild;
        addEventListenersToHearingGroup(newHearing);
        
        // Show all remove hearing buttons when there's more than one hearing
        updateRemoveHearingButtonsVisibility();
    });

    // Function to add event listeners to the initial hearing group
    function addInitialEventListeners() {
        const initialHearingGroup = document.querySelector('.hearing-group');
        addEventListenersToHearingGroup(initialHearingGroup);
    }

    // Function to add event listeners to a hearing group
    function addEventListenersToHearingGroup(hearingGroup) {
        // Add file button
        const addFileBtn = hearingGroup.querySelector('.add-file-btn');
        const filesContainer = hearingGroup.querySelector('.files-container');
        const hearingIndex = Array.from(hearingsContainer.children).indexOf(hearingGroup) + 1;
        
        let fileCounter = 1;
        
        addFileBtn.addEventListener('click', function() {
            // Count existing file inputs in this hearing
            fileCounter = filesContainer.children.length + 1;
            
            const fileInputDiv = document.createElement('div');
            fileInputDiv.className = 'file-input';
            fileInputDiv.innerHTML = `
                <label for="audio-file-${hearingIndex}-${fileCounter}">Audio File:</label>
                <input type="file" class="audio-file" id="audio-file-${hearingIndex}-${fileCounter}" name="audio-file-${hearingIndex}-${fileCounter}" accept=".mp3,.wav,.m4a,.ogg" required>
                <button type="button" class="remove-file-btn">Remove</button>
            `;
            
            filesContainer.appendChild(fileInputDiv);
            
            // Add event listener to new remove button
            const removeBtn = fileInputDiv.querySelector('.remove-file-btn');
            removeBtn.addEventListener('click', function() {
                filesContainer.removeChild(fileInputDiv);
                updateRemoveFileButtonsVisibility(filesContainer);
            });
            
            updateRemoveFileButtonsVisibility(filesContainer);
        });
        
        // Remove hearing button
        const removeHearingBtn = hearingGroup.querySelector('.remove-hearing-btn');
        removeHearingBtn.addEventListener('click', function() {
            hearingsContainer.removeChild(hearingGroup);
            updateRemoveHearingButtonsVisibility();
        });
        
        // Handle file removal buttons
        const initialRemoveFileBtn = hearingGroup.querySelector('.remove-file-btn');
        initialRemoveFileBtn.addEventListener('click', function(e) {
            const fileInput = e.target.closest('.file-input');
            filesContainer.removeChild(fileInput);
            updateRemoveFileButtonsVisibility(filesContainer);
        });
    }

    // Function to update the visibility of remove file buttons
    function updateRemoveFileButtonsVisibility(filesContainer) {
        const fileInputs = filesContainer.querySelectorAll('.file-input');
        if (fileInputs.length > 1) {
            fileInputs.forEach(input => {
                input.querySelector('.remove-file-btn').style.display = 'inline-block';
            });
        } else if (fileInputs.length === 1) {
            fileInputs[0].querySelector('.remove-file-btn').style.display = 'none';
        }
    }

    // Function to update the visibility of remove hearing buttons
    function updateRemoveHearingButtonsVisibility() {
        const hearingGroups = hearingsContainer.querySelectorAll('.hearing-group');
        if (hearingGroups.length > 1) {
            hearingGroups.forEach(group => {
                group.querySelector('.remove-hearing-btn').style.display = 'inline-block';
            });
        } else if (hearingGroups.length === 1) {
            hearingGroups[0].querySelector('.remove-hearing-btn').style.display = 'none';
        }
    }

    // Handle form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const hearingGroups = document.querySelectorAll('.hearing-group');
        
        // Check if we have valid input
        let hasFiles = false;
        let allDatesProvided = true;
        
        for (const hearingGroup of hearingGroups) {
            const hearingDate = hearingGroup.querySelector('.hearing-date').value;
            const fileInputs = hearingGroup.querySelectorAll('.audio-file');
            
            if (!hearingDate) {
                allDatesProvided = false;
            }
            
            for (const input of fileInputs) {
                if (input.files.length > 0) {
                    hasFiles = true;
                    break;
                }
            }
            
            if (hasFiles) break;
        }
        
        if (!allDatesProvided) {
            alert('Please select a date for each hearing');
            return;
        }
        
        if (!hasFiles) {
            alert('Please select at least one audio file');
            return;
        }
        
        // Show progress bar
        uploadBtn.disabled = true;
        uploadProgress.style.display = 'block';
        progressBar.style.width = '0%';
        
        // Upload files and collect file IDs for each hearing
        const hearingData = [];
        let totalFilesCount = 0;
        let filesProcessed = 0;
        
        // Count total files first for progress calculation
        for (const hearingGroup of hearingGroups) {
            const fileInputs = hearingGroup.querySelectorAll('.audio-file');
            for (const input of fileInputs) {
                if (input.files.length > 0) {
                    totalFilesCount++;
                }
            }
        }
        
        // Process each hearing group
        for (const hearingGroup of hearingGroups) {
            const hearingDate = hearingGroup.querySelector('.hearing-date').value;
            const fileInputs = hearingGroup.querySelectorAll('.audio-file');
            const hearingFiles = [];
            
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
                    hearingFiles.push(data.file_id);
                    
                    // Update progress
                    filesProcessed++;
                    const progress = Math.round((filesProcessed / totalFilesCount) * 50); // First 50% for uploads
                    progressBar.style.width = `${progress}%`;
                    
                } catch (error) {
                    console.error('Error uploading file:', error);
                    alert(`Error uploading file: ${error.message}`);
                    uploadBtn.disabled = false;
                    uploadProgress.style.display = 'none';
                    return;
                }
            }
            
            if (hearingFiles.length > 0) {
                hearingData.push({
                    hearing_date: hearingDate,
                    file_ids: hearingFiles
                });
            }
        }
        
        // Transcribe audio files for all hearings
        try {
            progressBar.style.width = '50%'; // Start second half of progress (transcription)
            
            const allTranscriptions = [];
            
            // Process each hearing's transcription
            for (const hearing of hearingData) {
                const transcribeResponse = await fetch('http://localhost:8000/transcribe/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        hearing_date: hearing.hearing_date,
                        file_ids: hearing.file_ids
                    })
                });
                
                if (!transcribeResponse.ok) {
                    throw new Error(`Transcription failed: ${transcribeResponse.statusText}`);
                }
                
                const transcriptions = await transcribeResponse.json();
                allTranscriptions.push(...transcriptions);
            }
            
            // Update progress to 100%
            progressBar.style.width = '100%';
            
            // Display transcription results
            displayTranscriptions(allTranscriptions);
            
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
        // Store transcriptions for report generation
        window.currentTranscriptions = transcriptions;
        
        transcriptionsContainer.innerHTML = '';
        
        if (transcriptions.length === 0) {
            transcriptionsContainer.innerHTML = '<p>No transcriptions found.</p>';
            return;
        }
        
        // Group transcriptions by hearing date
        const transcriptionsByDate = {};
        
        for (const item of transcriptions) {
            const date = item.hearing_date;
            if (!transcriptionsByDate[date]) {
                transcriptionsByDate[date] = [];
            }
            transcriptionsByDate[date].push(item);
        }
        
        // Display transcriptions grouped by hearing date
        for (const date in transcriptionsByDate) {
            const dateItems = transcriptionsByDate[date];
            
            // Create hearing date section with updated class names
            const dateSection = document.createElement('div');
            dateSection.className = 'hearing-date-section';
            dateSection.innerHTML = `
                <h3 class="hearing-date-heading">Hearing Date: ${date}</h3>
                <div class="hearing-transcriptions"></div>
            `;
            
            const hearingTranscriptions = dateSection.querySelector('.hearing-transcriptions');
            
            // Add each transcription for this date
            for (const item of dateItems) {
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
                    <h4>Transcription for File ID: ${item.file_id.substring(0, 8)}...</h4>
                    ${statutesSummary}
                    <div class="transcription-text">
                        ${item.highlighted_transcription || item.transcription}
                    </div>
                `;
                
                hearingTranscriptions.appendChild(transcriptionDiv);
                
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
            }
            
            transcriptionsContainer.appendChild(dateSection);
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
        // Reset form and hearing counter
        uploadForm.reset();
        hearingCounter = 1;
        
        // Clear existing hearing groups
        hearingsContainer.innerHTML = '';
        
        // Add back first hearing group
        const hearingGroup = document.createElement('div');
        hearingGroup.className = 'hearing-group';
        hearingGroup.innerHTML = `
            <div class="hearing-header">
                <h3>Hearing #1</h3>
                <button type="button" class="remove-hearing-btn" style="display:none;">Remove Hearing</button>
            </div>
            <div class="form-group">
                <label for="hearing-date-1">Hearing Date:</label>
                <input type="date" class="hearing-date" id="hearing-date-1" name="hearing-date-1" required value="${today}">
            </div>
            
            <div class="files-container">
                <div class="file-input">
                    <label for="audio-file-1-1">Audio File:</label>
                    <input type="file" class="audio-file" id="audio-file-1-1" name="audio-file-1-1" accept=".mp3,.wav,.m4a,.ogg" required>
                    <button type="button" class="remove-file-btn" style="display:none;">Remove</button>
                </div>
            </div>

            <button type="button" class="add-file-btn">+ Add Another Audio Part for this Same Hearing Date</button>
        `;
        
        hearingsContainer.appendChild(hearingGroup);
        addEventListenersToHearingGroup(hearingGroup);
        
        // Hide results and show upload form
        resultsSection.style.display = 'none';
        document.getElementById('upload-section').style.display = 'block';
    });
    
    // Download report button
    downloadReportBtn.addEventListener('click', function() {
        if (!window.currentTranscriptions || window.currentTranscriptions.length === 0) {
            alert('No transcription data available to generate a report');
            return;
        }
        
        showExportOptionsModal();
    });
    
    // Show export options modal
    function showExportOptionsModal() {
        const modalContainer = document.createElement('div');
        modalContainer.className = 'export-options-modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'export-options-content';
        
        modalContent.innerHTML = `
            <div class="export-options-header">
                <h3>Export Report</h3>
                <button class="close-modal">×</button>
            </div>
            <div class="export-options-body">
                <p>Choose a format for your transcription and statute analysis report:</p>
                
                <div class="export-format-options">
                    <div class="export-format-option selected" data-format="pdf">
                        <input type="radio" name="export-format" id="pdf-format" value="pdf" checked>
                        <div class="export-format-icon">PDF</div>
                        <div class="export-format-details">
                            <label for="pdf-format">PDF Document</label>
                            <p>Well-formatted document with complete analysis and statute comparisons</p>
                        </div>
                    </div>
                    
                    <div class="export-format-option" data-format="json">
                        <input type="radio" name="export-format" id="json-format" value="json">
                        <div class="export-format-icon">JSON</div>
                        <div class="export-format-details">
                            <label for="json-format">JSON Data</label>
                            <p>Machine-readable format for further processing or integration</p>
                        </div>
                    </div>
                </div>
                
                <div class="export-options-actions">
                    <button id="generate-report-btn" class="primary-button">Generate Report</button>
                    <button class="cancel-button close-modal">Cancel</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modalContainer);
        
        // Add event listeners
        const closeButtons = modalContent.querySelectorAll('.close-modal');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                document.body.removeChild(modalContainer);
            });
        });
        
        // Format option selection
        const formatOptions = modalContent.querySelectorAll('.export-format-option');
        formatOptions.forEach(option => {
            option.addEventListener('click', function() {
                formatOptions.forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
                this.querySelector('input[type="radio"]').checked = true;
            });
        });
        
        // Generate report button
        const generateReportBtn = modalContent.querySelector('#generate-report-btn');
        generateReportBtn.addEventListener('click', async function() {
            const selectedFormat = modalContent.querySelector('input[name="export-format"]:checked').value;
            
            // Show loading state
            this.textContent = 'Generating...';
            this.disabled = true;
            
            try {
                const response = await fetch('http://localhost:8000/generate-report/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        format: selectedFormat,
                        transcriptions: window.currentTranscriptions,
                        metadata: {
                            generated_by: "CourtCaseVibe User",
                            generation_date: new Date().toISOString()
                        }
                    })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `Error generating report: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                // Remove the modal
                document.body.removeChild(modalContainer);
                
                // Show success message with link to download
                alert(`Report generated successfully! Saved to: ${data.file_path}`);
                
                // Open the file location (this will depend on browser and OS)
                window.open(`http://localhost:8000/download-report/?path=${encodeURIComponent(data.file_path)}`);
                
            } catch (error) {
                console.error('Error generating report:', error);
                alert(`Error generating report: ${error.message}`);
                this.textContent = 'Generate Report';
                this.disabled = false;
            }
        });
        
        // Append modal to container and body
        modalContainer.appendChild(modalContent);
        
        // Close when clicking outside the modal
        modalContainer.addEventListener('click', function(e) {
            if (e.target === modalContainer) {
                document.body.removeChild(modalContainer);
            }
        });
    }
});
