document.addEventListener("DOMContentLoaded", function() {
    let countdown = false;
    let countdownInterval;
    const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    const cancellationModal = new bootstrap.Modal(document.getElementById('cancellationModal'));
    let exit_initiatedByJitsi = false;
    let lastJitsiEventTime = 0; // Timestamp of the last Jitsi event
    const DEBOUNCE_DELAY = 10000;

    const options = {
        roomName: '{{ conference.url }}',  // Conference room name
        width: '100%',
        height: '100%',
        jwt: '{{ jwt }}',
        parentNode: document.querySelector('#jitsi-container'),
        configOverwrite: { 
            startWithAudioMuted: false,
            prejoinPageEnabled: false,
            disableDeepLinking: true
        },
        interfaceConfigOverwrite: { filmStripOnly: false }
    };
    const api = new JitsiMeetExternalAPI('{{ VIDEO_HOST_DOMAIN }}', options);

    api.addListener('videoConferenceLeft', function() {
        const now = Date.now();
        console.log('Conference left', now - lastJitsiEventTime);

        if (now - lastJitsiEventTime > DEBOUNCE_DELAY) {
            lastJitsiEventTime = now;
            resetCooldown();
            startCooldown('Video conference ended', true);
        }
    });
    
    // Fullscreen toggle
    document.getElementById('fullscreen-toggle').addEventListener('click', function() {
        const iframe = document.getElementById('jitsi-container');
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            iframe.requestFullscreen().catch(err => console.log(err));
        }
    });

    {% if session['current_role'] == 'clinician' %}
    // Handle consultation completion
    document.getElementById('complete-consult').addEventListener('click', function() {
        if (document.getElementById('sign-toggle').textContent != 'Unsign') {
            alert("Please sign the prescription before completing the consultation.");
        } else {
            // Show the confirmation modal
            confirmationModal.show();
            startCooldown('Consultation completed', false);
        }
    });

    // Handle Consultation Cancellation
    document.getElementById('cancel-consult').addEventListener('click', function() {
        cancellationModal.show();
    });

    // Handle Consultation Cancellation
    // Show the new confirmation modal when 'pause-consult' is clicked
    document.getElementById('pause-consult').addEventListener('click', function() {
        startCooldown('Consultation completed', false);
    });

    // Handle the confirmation button click in the new modal
    document.getElementById('confirm-cancellation').addEventListener('click', function() {
        // Proceed with the action
        exitFunction(2); // Call your function or action
    });

    document.getElementById('cancel-cancellation').addEventListener('click', function() {
        // Cancel the countdown and reset variables
        cancellationModal.hide();
        resetCooldown();
    });
    {% endif %}

    document.getElementById('confirm-exit').addEventListener('click', function() {
        // Continue the countdown and execute the redirect
        countdownInterval = 0;
        confirmationModal.hide();
    });

    document.getElementById('cancel-exit').addEventListener('click', function() {
        // Cancel the countdown and reset variables
        confirmationModal.hide();
        resetCooldown();
    });

    document.getElementById('confirmationModal').addEventListener('hidden.bs.modal', function() {
        if (exit_initiatedByJitsi && countdown) {
            location.reload();
        }
    });
    
    function resetCooldown() {
        if (exit_initiatedByJitsi && countdown) {
            location.reload();
        }
        countdown = false;
        countdownInterval = 3;
        exit_initiatedByJitsi = false;
        confirmationModal.hide();
    }
    
    function startCooldown(reason, initiatedByJitsi = false) {
        exit_initiatedByJitsi = initiatedByJitsi;
        countdown = true;
        let timeLeft = 3;
        document.getElementById('cooldown-timer').textContent = `Redirecting in ${timeLeft} seconds...`;
        confirmationModal.show();
    
        let countdownProcess = setInterval(function() {
            timeLeft--;
            document.getElementById('cooldown-timer').textContent = `Redirecting in ${timeLeft} seconds...`;
            if (timeLeft <= 0) {
                clearInterval(countdownProcess);
                handleCooldownCompletion();
            }
        }, 1000);
    }
    
    function handleCooldownCompletion() {
        if (countdown && exit_initiatedByJitsi) {
            window.location.href = '{{ lobby_url }}';
        } else if (countdown) {
            exitFunction(1);
        } else {
            resetCooldown();
        }
    }
    

    let currentDrugId = null;
    let autocompleteDrugs = [];
    let fetchedInstructions = [];
    const appointmentId = document.getElementById('appointment-id').value;

    // Function to initialize autocompletion for drugs
    function initAutocomplete() {
        const drugInput = document.getElementById('new-prescription-drug');
        const drugSuggestions = document.getElementById('drug-suggestions');
        const originalBorderColor = drugInput.style.borderColor;

        // Show suggestions when input is focused
        drugInput.addEventListener('focus', function() {
            drugSuggestions.style.display = 'block';
            drugInput.classList.remove('input-invalid');
            $(drugInput).popover('dispose'); 
        });

        // Hide suggestions when input loses focus
        drugInput.addEventListener('blur', function() {
            setTimeout(() => { // Delay hiding to allow click event on suggestions
                drugSuggestions.style.display = 'none';
            }, 200);

            // Find if the current input matches any of the suggestions
            const inputValue = drugInput.value.toLowerCase();
            const match = autocompleteDrugs.find(drug => drug.name.toLowerCase() === inputValue);

            if (match) {
                // If a match is found, set data attributes
                drugInput.dataset.drugId = match.id;
                drugInput.dataset.drugName = match.name;
            }

            // Check if the input matches any of the stored suggestions
            const drugName = drugInput.dataset.drugName;
            if (drugName && drugInput.value.toLowerCase() !== drugName.toLowerCase()) {
                // If input does not match the stored drug name, remove data attributes
                drugInput.removeAttribute('data-drug-id');
                drugInput.removeAttribute('data-drug-name');
            }

            // If no drugId is set, show the invalid styling and popover
            if (!drugInput.dataset.drugId && drugInput.value.length > 0) {
                drugInput.classList.add('input-invalid'); // Add invalid styling
                $(drugInput).popover({
                    html: true,
                    content: `
                        <div>
                            <span>Not in library.</span> <span id="create-drug-btn" class="btn btn-sm btn-primary">create now?</span>
                        </div>
                    `,
                    placement: 'bottom',
                    trigger: 'manual'
                }).popover('show');

                // Add click event listener to the "Create Now" button
                $(document).on('click', '#create-drug-btn', function() {
                    const drugName = drugInput.value;
                    if (confirm(`Do you want to create a new drug with the name "${drugName}"?`)) {
                        createNewDrug(drugName, drugInput);
                    }
                });
            }
        });

        drugInput.addEventListener('input', function() {
            const autocompleteList = document.getElementById('drug-suggestions');
            autocompleteList.innerHTML = '';
            const query = drugInput.value;
            if (query.length < 2){
                return;
            }

            fetch(`/emr/drugs/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    autocompleteDrugs = data;
                    data.forEach(drug => {
                        const option = document.createElement('div');
                        option.classList.add('autocomplete-item');
                        option.textContent = drug.name;
                        option.dataset.drugId = drug.id;
                        option.dataset.drugName = drug.name;
                        option.addEventListener('click', function() {
                            drugInput.value = drug.name;
                            drugInput.dataset.drugId = drug.id;
                            drugInput.dataset.drugName = drug.name;
                            drugInput.focus();
                            fillInstructions(drug.id);
                            autocompleteList.innerHTML = '';
                            
                        });
                        autocompleteList.appendChild(option);
                    });
                });
        });

        // Check if the input value matches any autocomplete suggestion
        drugInput.addEventListener('blur', function() {
            const query = drugInput.value;
            const matchedDrug = autocompleteDrugs.find(drug => drug.name.toLowerCase() === query.toLowerCase());
            if (matchedDrug) {
                drugInput.dataset.drugId = matchedDrug.id;
                fillInstructions(matchedDrug.id);
            }
        });

    }

    // Function to initialize instruction autocomplete
    function initInstructionAutocomplete() {
        const instructionInput = document.getElementById('new-prescription-instruction');
        const instructionSuggestions = document.getElementById('instruction-suggestions');

        // Show suggestions when input is focused
        instructionInput.addEventListener('focus', function() {
            instructionSuggestions.style.display = 'block';
        });

        // Hide suggestions when input loses focus
        instructionInput.addEventListener('blur', function() {
            setTimeout(() => { // Delay hiding to allow click event on suggestions
                instructionSuggestions.style.display = 'none';
            }, 200);
        });

        instructionInput.addEventListener('input', function() {
            instructionSuggestions.innerHTML = '';
            const query = instructionInput.value;
            if (query.length < 2) {
                return;
            }

            const filteredInstructions = fetchedInstructions.filter(instruction => 
                instruction.instruction.toLowerCase().includes(query.toLowerCase())
            );
            filteredInstructions.slice(0, 5).forEach(instruction => { // Limit to 5 suggestions
                const option = document.createElement('div');
                option.classList.add('autocomplete-item');
                option.textContent = instruction.instruction;
                option.addEventListener('click', function() {
                    instructionInput.value = instruction.instruction;
                    instructionSuggestions.innerHTML = '';
                    instructionSuggestions.style.display = 'none';
                });
                instructionSuggestions.appendChild(option);
            });
            positionSuggestions(instructionInput, instructionSuggestions);
        });
    }

    // Function to fill instructions for selected drug
    function fillInstructions(drugId) {
        // If the drugId has not changed, do nothing
        if (drugId === currentDrugId) {
            return;
        }

        currentDrugId = drugId;
        
        const instructionInput = document.getElementById('new-prescription-instruction');
        fetch(`/emr/drugs/${encodeURIComponent(drugId)}/instructions`)
            .then(response => response.json())
            .then(data => {
                fetchedInstructions = data; // Store fetched instructions
                updateInstructionSuggestions(''); // Show all suggestions initially

                // Add event listener for filtering suggestions based on input
                instructionInput.addEventListener('input', function() {
                    const query = instructionInput.value;
                    updateInstructionSuggestions(query);
                });
            });
    }

    // Function to update the instruction suggestions based on input
    function updateInstructionSuggestions(query) {
        const instructionList = document.getElementById('instruction-suggestions');
        instructionList.innerHTML = '';
        const filteredInstructions = fetchedInstructions.filter(instruction => 
            instruction.instruction.toLowerCase().includes(query.toLowerCase())
        );
        filteredInstructions.forEach(instruction => {
            const option = document.createElement('div');
            option.classList.add('autocomplete-item');
            option.textContent = instruction.instruction;
            option.addEventListener('click', function() {
                document.getElementById('new-prescription-instruction').value = instruction.instruction;
                instructionList.innerHTML = '';
            });
            instructionList.appendChild(option);
        });
        instructionInput.focus();
    }

    function createNewDrug(drugName, drugInput) {
        fetch('/emr/drugs/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: drugName }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.id && data.name) {
                drugInput.dataset.drugId = data.id;
                drugInput.dataset.drugName = data.name;
                drugInput.value = data.name;
                drugInput.focus();  // Set focus back to the input
                $(drugInput).popover('dispose');  // Hide the popover

                // Show a success tooltip
                $(drugInput).tooltip({
                    title: 'Library updated!',
                    placement: 'bottom',
                    trigger: 'manual'
                }).tooltip('show');

                // Automatically hide the tooltip after 2 seconds
                setTimeout(() => {
                    $(drugInput).tooltip('hide');
                }, 2000);
                
            } else {
                alert('Error creating new drug.');
            }
        })
        .catch(error => {
            alert('Error creating new drug.');
            console.error('Error:', error);
        });
    }

    // Function to add new prescription to the list
    function addNewPrescription() {
        const drugInput = document.getElementById('new-prescription-drug');
        const instructionInput = document.getElementById('new-prescription-instruction');
        const durationInput = document.getElementById('new-prescription-duration');
        const prescriptionList = document.getElementById('prescription-list');

        if (!drugInput.value || !instructionInput.value || !durationInput.value) {
            alert('Please fill in all fields');
            return;
        }

        const drugId = drugInput.dataset.drugId;
        const drugName = drugInput.value;
        const instruction = instructionInput.value;
        const duration = durationInput.value;

        const newRow = document.createElement('tr');
        newRow.classList.add('prescription-entry');
        newRow.dataset.drugId = drugId;
        newRow.innerHTML = `
            <td>${drugName}</td> 
            <td>${instruction}</td>
            <td>${duration}</td>
            <td><button class="btn btn-danger btn-sm remove-prescription">Remove</button></td>
        `;
        prescriptionList.appendChild(newRow);

        // Clear input fields
        drugInput.value = '';
        instructionInput.value = '';
        durationInput.value = '';
        document.getElementById('add-prescription-btn').disabled = true;
    }

    // Function to remove a prescription from the list
    function removePrescription(event) {
        if (event.target.classList.contains('remove-prescription')) {
            event.target.closest('.prescription-entry').remove();
        }
    }

    // Function to enable add button when all fields are filled
    function enableAddButton() {
        const drugInput = document.getElementById('new-prescription-drug');
        const instructionInput = document.getElementById('new-prescription-instruction');
        const durationInput = document.getElementById('new-prescription-duration');
        const addButton = document.getElementById('add-prescription-btn');
        console.log(drugInput.value, instructionInput.value, durationInput.value)
        if (drugInput.value && instructionInput.value && durationInput.value) {
            addButton.disabled = false;
        } else {
            addButton.disabled = true;
        }
    }

    // Form submission event handler
    function handleFormSubmission(event) {
        event.preventDefault();
        
        // Gather data from all tabs and inputs
        const reason = document.getElementById('reason').value;
        const history = document.getElementById('history').value;
        const findings = document.getElementById('findings').value;
        const plan_note = document.getElementById('management-notes').value;

        // Gather prescription data from dynamically generated elements
        const prescriptions = Array.from(document.querySelectorAll('#prescription-list tr.prescription-entry')).map(entry => ({
            drug_id: entry.dataset.drugId,  // Retrieve the data-drug-id attribute
            drug_name: entry.cells[0].textContent.trim(), // First cell contains the drug name
            instruction: entry.cells[1].textContent.trim(), // Second cell contains the instruction
            duration: entry.cells[2].textContent.trim(), // Third cell contains the duration
        }));

        // Create JSON payload
        const payload = {
            reason: reason,
            history: history,
            findings: findings,
            prescriptions: prescriptions,
            plan_note: plan_note
        };
        
        const url = `/appointment/${appointmentId}/plan`;
        console.log(payload);
        console.log(appointmentId);
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Create new button to preview the generated document

                let previewButton = document.getElementById('preview-plan');
                if (!previewButton) {
                    // Create new button if it does not exist
                    previewButton = document.createElement('button');
                    previewButton.id = 'preview-plan';
                    previewButton.className = 'btn btn-info';
                    previewButton.textContent = 'View Prescription';
                    
                    // Insert the button before the "Sign" button
                    const signButton = document.getElementById('sign-toggle');
                    const parent = signButton.parentNode;
                    parent.insertBefore(previewButton, signButton);
                }

                // Function to show the modal with the document
                const showPreview = (url) => {
                    const modal = document.getElementById('previewModal');
                    const iframe = document.getElementById('previewIframe');
                    const closeBtn = document.getElementById('previewClose');
                    const signButton = document.getElementById('sign-toggle');
                    signButton.classList.add('button-over-modal');
                    // Set iframe source to document URL
                    iframe.src = url;
        
                    // Display the modal
                    modal.style.display = 'block';
        
                    // Close the modal when the close button is clicked
                    closeBtn.onclick = () => {
                        modal.style.display = 'none';
                        iframe.src = ''; 
                        signButton.classList.remove('button-over-modal');
                    };
        
                    // Close the modal when clicking outside of it
                    window.onclick = (event) => {
                        if (event.target === modal) {
                            modal.style.display = 'none';
                            iframe.src = '';
                            signButton.classList.remove('button-over-modal');
                        }
                    };
                };
        
                // Set the onclick behavior for the preview button
                previewButton.onclick = () => showPreview(data.document_url);
        
                previewButton.click();
            } else {
                alert('There was an error generating the plan.');
            }
        });
    }

    // Handle Sign Toggle
    function handleSignToggle() {
        const signButton = document.getElementById('sign-toggle');
        const signState = signButton.textContent === 'Sign';
        let generateButton = document.getElementById('generate-prescription')
        let previewButton = document.getElementById('preview-plan');
        let completeButton = document.getElementById('complete-consult');
        // Check the condition for button-over-modal class
        if (signState && signButton.classList.contains('button-over-modal')) {
            fetch(`{{ url_for('consult.sign_prescription', appointment_id=conference.appointment_id) }}`, {
                method: 'POST',
                body: JSON.stringify({ signed: true }),
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin'
            }).then(() => {
                // Change button text to "Unsign" and apply dull color
                signButton.textContent = 'Unsign';
                signButton.style.backgroundColor = '#dc3545'; // Dull color
                signButton.style.color = '#FFF';
                completeButton.style.backgroundColor = '#28a745';
                completeButton.disabled = false;
                generateButton.disabled = true;
            });
        } else if (signState && !signButton.classList.contains('button-over-modal')) {
            // Simulate a click on the preview button
            
            if (previewButton) {
                previewButton.click();
            }
        } else if (!signState) {
            fetch(`{{ url_for('consult.sign_prescription', appointment_id=conference.appointment_id) }}`, {
                method: 'POST',
                body: JSON.stringify({ signed: false }),
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin'
            }).then(() => {
                // Change button text to "Sign" and reset color
                signButton.textContent = 'Sign';
                signButton.style.backgroundColor = ''; // Reset to original color
                signButton.style.color = ''; // Reset text color
                completeButton.style.backgroundColor = '#777';
                completeButton.disabled = true;
                generateButton.disabled = false;
            });
        }
    }
    
    function exitFunction(conclusion) {
        // conclusion 1 = complete, 0 = do nothing, 1 = canceled properly
        fetch("{{ url_for('consult.conclude_appointment', appointment_id=conference.appointment_id) }}", {
            method: 'POST',
            body: JSON.stringify({ conclusion: conclusion }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin'
        }).then(response => {
            // Check if the response status is OK (status in the range 200-299)
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            // Parse the JSON response
            return response.json();
        })
        .then(data => {
            // Check if the response JSON contains success: true
            if (data.success) {
                // Redirect to the lobby URL if success
                window.location.href = '{{ lobby_url }}';
            } else {
                // Alert if success is false
                alert('Completion failed');
            }
        })
        .catch(error => {
            // Handle any errors that occurred during fetch
            console.error('There was a problem with the fetch operation:', error);
            alert('An error occurred while processing your request.');
        });
    }
    
    


    // Event Listeners
    document.getElementById('new-prescription-drug').addEventListener('input', enableAddButton);
    document.getElementById('new-prescription-instruction').addEventListener('input', enableAddButton);
    document.getElementById('new-prescription-duration').addEventListener('input', enableAddButton);
    document.getElementById('add-prescription-btn').addEventListener('click', addNewPrescription);
    document.getElementById('prescription-list').addEventListener('click', removePrescription);
    document.getElementById('generate-prescription').addEventListener('click', handleFormSubmission);
    document.getElementById('sign-toggle').addEventListener('click', handleSignToggle);


    initAutocomplete();
    initInstructionAutocomplete();
});
