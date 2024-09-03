document.addEventListener("DOMContentLoaded", function() {
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
                const previewButton = document.createElement('button');
                previewButton.id = 'preview-plan';
                previewButton.className = 'btn btn-info';
                previewButton.textContent = 'Preview Plan';
                previewButton.onclick = () => window.open(data.document_url, '_blank');

                // Append the new button to the control panel
                document.querySelector('.consultation-controls').appendChild(previewButton);

                // Simulate a click on the preview button
                previewButton.click();
            } else {
                alert('There was an error generating the plan.');
            }
        });
    }

    // Event Listeners
    document.getElementById('new-prescription-drug').addEventListener('input', enableAddButton);
    document.getElementById('new-prescription-instruction').addEventListener('input', enableAddButton);
    document.getElementById('new-prescription-duration').addEventListener('input', enableAddButton);
    document.getElementById('add-prescription-btn').addEventListener('click', addNewPrescription);
    document.getElementById('prescription-list').addEventListener('click', removePrescription);
    document.getElementById('generate-prescription').addEventListener('click', handleFormSubmission);

    initAutocomplete();
    initInstructionAutocomplete();
});
