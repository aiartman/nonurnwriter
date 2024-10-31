document.addEventListener('DOMContentLoaded', function() {
    const uploadBtn = document.getElementById('uploadBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const csvFileInput = document.getElementById('csvFile');
    const fileNameDisplay = document.getElementById('fileName');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const totalEmailsDisplay = document.getElementById('totalEmails');
    const avgProcessingTimeDisplay = document.getElementById('avgProcessingTime');
    const downloadContainer = document.getElementById('downloadContainer');
    const downloadBtn = document.getElementById('downloadBtn');
    const historyList = document.getElementById('historyList');
    const currentFile = document.getElementById('currentFile');
    const timeRemaining = document.getElementById('timeRemaining');
    const timeElapsed = document.getElementById('timeElapsed');
    const avgTimePerEmail = document.getElementById('avgTimePerEmail');
    const timeLeftElement = document.getElementById('timeLeft');
    // ... other element references ...

    let startTime;
    let intervalId;

    // File input change event
    csvFileInput.addEventListener('change', (e) => {
        fileNameDisplay.textContent = e.target.files[0] ? e.target.files[0].name : 'No file chosen';
    });

    // Upload button click event
    uploadBtn.addEventListener('click', () => {
        const file = csvFileInput.files[0];
        if (file) {
            processFile(file);
        } else {
            alert('Please select a CSV file');
        }
    });

    function processFile(file) {
        // Hide/Show appropriate elements
        progressContainer.classList.remove('hidden');
        uploadBtn.classList.add('hidden');
        cancelBtn.classList.remove('hidden');

        startTime = Date.now();

        const formData = new FormData();
        formData.append('csv_file', file);

        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                currentFile.innerHTML = `<i class="fas fa-file-csv mr-2"></i>Processing: <span class="font-semibold">${file.name}</span>`;
                startProgressTracking();
                checkStatus();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                resetUI();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
            resetUI();
        });
    }

    function startProgressTracking() {
        startTime = Date.now();
        intervalId = setInterval(updateTimeInfo, 1000);
    }

    function updateTimeInfo() {
        const currentTime = Date.now();
        const elapsedTime = Math.floor((currentTime - startTime) / 1000); // in seconds
        timeElapsed.textContent = formatTime(elapsedTime);

        // Calculate estimated time left
        const progress = parseInt(progressText.textContent);
        if (progress > 0) {
            const totalEstimatedTime = (elapsedTime / progress) * 100;
            const timeLeft = Math.max(0, Math.floor(totalEstimatedTime - elapsedTime));
            timeLeftElement.textContent = formatTime(timeLeft);
        } else {
            timeLeftElement.textContent = 'Calculating...';
        }
    }

    function formatTime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;

        let formattedTime = '';

        if (days > 0) {
            formattedTime += `${days}d `;
        }

        if (days > 0 || hours > 0) {
            formattedTime += `${padZero(hours)}h `;
        }

        formattedTime += `${padZero(minutes)}m ${padZero(remainingSeconds)}s`;

        return formattedTime.trim();
    }

    function padZero(num) {
        return num.toString().padStart(2, '0');
    }

    function checkStatus() {
        // Poll the backend for progress
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                if (data.state === 'PROGRESS') {
                    // Update progress bar and text
                    progressBar.style.width = `${data.progress}%`;
                    progressText.textContent = `${data.progress}%`;

                    setTimeout(checkStatus, 1000);
                } else if (data.state === 'SUCCESS') {
                    // Processing complete
                    progressBar.style.width = `100%`;
                    progressText.textContent = `100%`;
                    finishProcessing(data.result);
                } else if (data.state === 'FAILURE') {
                    alert('An error occurred during processing.');
                    resetUI();
                } else {
                    setTimeout(checkStatus, 1000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while checking status. Please try again.');
                resetUI();
            });
    }

    function finishProcessing(result) {
        // Hide/Show appropriate elements
        downloadContainer.classList.remove('hidden');
        uploadBtn.classList.remove('hidden');
        cancelBtn.classList.add('hidden');

        // Update statistics
        const totalTime = (Date.now() - startTime) / 1000;
        updateStatistics(result.total_emails_generated, totalTime);

        // Optionally, add to history
        addToHistory(result.file_name, totalTime, result.total_emails_generated);

        clearInterval(intervalId); // Stop updating time info
    }

    function resetUI() {
        progressContainer.classList.add('hidden');
        uploadBtn.classList.remove('hidden');
        cancelBtn.classList.add('hidden');
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        currentFile.innerHTML = '';
        timeElapsed.textContent = '00:00:00';
        timeLeftElement.textContent = 'Calculating...';
        clearInterval(intervalId);
    }

    function updateStatistics(emailCount, totalTime) {
        // Update total emails and average processing time
        const currentTotal = parseInt(totalEmailsDisplay.textContent);
        const newTotal = currentTotal + emailCount;
        totalEmailsDisplay.textContent = newTotal;

        const currentAvg = parseFloat(avgProcessingTimeDisplay.textContent) || 0;
        const newAvg = ((currentAvg * currentTotal) + totalTime) / newTotal;
        avgProcessingTimeDisplay.textContent = newAvg.toFixed(2) + ' s';
    }

    // **Add the missing addToHistory function**
    function addToHistory(fileName, totalTime, emailCount) {
        const row = document.createElement('tr');
        const dateProcessed = new Date().toLocaleString();
        row.innerHTML = `
            <td class="py-2 px-4 border-b dark:border-gray-700">${fileName}</td>
            <td class="py-2 px-4 border-b dark:border-gray-700">${dateProcessed}</td>
            <td class="py-2 px-4 border-b dark:border-gray-700">${emailCount}</td>
            <td class="py-2 px-4 border-b dark:border-gray-700">${totalTime.toFixed(2)} seconds</td>
            <td class="py-2 px-4 border-b dark:border-gray-700"><span class="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300 py-1 px-2 rounded-full text-xs">Completed</span></td>
        `;
        historyList.prepend(row);
    }

    // If you have other functions, make sure they are properly defined
    // For example, if you have functionality for downloading the generated emails
    downloadBtn.addEventListener('click', function(event) {
        event.preventDefault();
        
        fetch('/download_csv')
            .then(response => {
                if (response.ok) {
                    return response.blob();
                }
                return response.json().then(err => Promise.reject(err));
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'linkedin_emails.csv';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to download CSV. ' + (error.error || 'Please try again.'));
            });
    });

    // Check for ongoing processes when the page loads
    checkOngoingProcess();

    function checkOngoingProcess() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                if (data.state === 'PROGRESS') {
                    // There's an ongoing process, update the UI
                    progressContainer.classList.remove('hidden');
                    uploadBtn.classList.add('hidden');
                    cancelBtn.classList.remove('hidden');
                    currentFile.innerHTML = `<i class="fas fa-file-csv mr-2"></i>Processing: <span class="font-semibold">${data.file_path}</span>`;
                    startProgressTracking();
                    checkStatus();
                }
            })
            .catch(error => console.error('Error:', error));
    }
});
