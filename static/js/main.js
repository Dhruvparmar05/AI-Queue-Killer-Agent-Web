const serviceMap = {
    'passport': [
        {val: 'fresh_passport', label: 'Fresh Passport Application Wizard', requireInput: false},
        {val: 'reissue_passport', label: 'Re-issue / Expired Passport Renewal', requireInput: false},
        {val: 'tatkaal_passport', label: 'Tatkaal Scheme Fast-Track Booking', requireInput: false},
        {val: 'pcc_application', label: 'Police Clearance Certificate (PCC) Service', requireInput: false},
        {val: 'check_appointment', label: 'Check PSK / POPSK Appointment Slots', requireInput: false},
        {val: 'track_status', label: 'Track Application Status (Auto-Inject ARN)', requireInput: true, placeholder: 'Enter 15-digit File Number / ARN'},
        {val: 'manage_appointment', label: 'Reschedule / Cancel Existing Appointment', requireInput: true, placeholder: 'Enter Appointment Reference ID'},
        {val: 'passport_advisor', label: 'Passport Fee & Document Advisor', requireInput: false}
    ],
    'rto': [
        {val: 'll_apply', label: 'Learner License (LL) New Application', requireInput: false},
        {val: 'll_slot', label: 'LL Computer Test Slot Booking', requireInput: true, placeholder: 'Enter LL Application Number'},
        {val: 'dl_apply', label: 'Permanent Driving License (DL) Application', requireInput: true, placeholder: 'Enter LL License Number'},
        {val: 'dl_slot', label: 'DL Practical Driving Slot Booking', requireInput: true, placeholder: 'Enter DL Application Number'},
        {val: 'dl_renewal', label: 'DL Renewal & Address/Name Change', requireInput: true, placeholder: 'Enter DL Number'},
        {val: 'pay_echallan', label: 'Check & Settle E-Challan / Traffic Fines', requireInput: true, placeholder: 'Enter Challan No. / Vehicle Reg. No.'},
        {val: 'rc_transfer', label: 'Vehicle RC Ownership Transfer (Form 29/30)', requireInput: true, placeholder: 'Enter Vehicle Registration Number'},
        {val: 'rc_hp_cancel', label: 'RC Hypothecation Removal (HP Cancel)', requireInput: true, placeholder: 'Enter Vehicle Registration Number'},
        {val: 'hsrp_booking', label: 'High-Security Registration Plate (HSRP) Booking', requireInput: true, placeholder: 'Enter Vehicle Reg / Chassis Number'}
    ],
    'ors': [
        {val: 'opd_appointment', label: 'Book AI OPD Doctor Consultation', requireInput: true, placeholder: 'Enter UHID / Mobile Number'},
        {val: 'dept_consultation', label: 'Department Specialization Consultation Lock', requireInput: true, placeholder: 'Enter Patient UHID'},
        {val: 'lab_reports', label: 'Fetch Diagnostic & Lab Pathology Reports', requireInput: true, placeholder: 'Enter Report Ref No. / UHID'},
        {val: 'radiology_status', label: 'Radiology Scan Status Fetcher', requireInput: true, placeholder: 'Enter Scan Reference Number'},
        {val: 'opd_card_reprint', label: 'OPD Registration Card Re-printing', requireInput: true, placeholder: 'Enter UHID / Registration ID'},
        {val: 'bed_availability', label: 'Real-time Hospital Bed & ICU Availability Scan', requireInput: false}
    ],
    'digital_gujarat': [
        {val: 'income_certificate', label: 'Income Certificate (આવકનો દાખલો) Service', requireInput: false},
        {val: 'caste_certificate', label: 'Caste Certificate & Non-Creamy Layer (NCL)', requireInput: false},
        {val: 'domicile_cert', label: 'Domicile & Solvency Certificate Gateway', requireInput: false},
        {val: 'scholarship_status', label: 'State Scholarship Status Tracking', requireInput: true, placeholder: 'Enter Scholarship Application ID'},
        {val: 'ration_card_service', label: 'Ration Card Member Addition/Deletion', requireInput: true, placeholder: 'Enter Ration Card Number'}
    ],
    'banking': [
        {val: 'bank_token', label: 'Branch e-Corner Online Queue Token Booking', requireInput: false},
        {val: 'doorstep_banking', label: 'Senior Citizen Doorstep Banking Scheduling', requireInput: true, placeholder: 'Enter Bank Account Number'},
        {val: 'life_certificate', label: 'Digital Life Certificate (Jeevan Pramaan)', requireInput: true, placeholder: 'Enter Pensioner PPO Number'}
    ]
};

function updateServices() {
    const portalSelect = document.getElementById('portalSelect');
    const serviceSelect = document.getElementById('serviceSelect');
    const dynamicInputContainer = document.getElementById('dynamicInputContainer');

    if (!portalSelect || !serviceSelect) return;

    const portal = portalSelect.value;
    serviceSelect.innerHTML = '<option value="">-- Choose Task Service --</option>';

    if (dynamicInputContainer) {
        dynamicInputContainer.style.display = 'none';
    }

    if (portal && serviceMap[portal]) {
        serviceMap[portal].forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.val;
            opt.textContent = item.label;
            opt.setAttribute('data-require-input', item.requireInput);
            opt.setAttribute('data-placeholder', item.placeholder || '');
            serviceSelect.appendChild(opt);
        });
    }
}

function handleServiceChange() {
    const serviceSelect = document.getElementById('serviceSelect');
    const dynamicInputContainer = document.getElementById('dynamicInputContainer');
    const dynamicInput = document.getElementById('dynamicInput');
    const inputLabel = document.getElementById('inputLabel');

    if (!serviceSelect || !dynamicInputContainer) return;

    const selectedOption = serviceSelect.options[serviceSelect.selectedIndex];
    const isRequired = selectedOption ? selectedOption.getAttribute('data-require-input') : "false";
    const placeholder = selectedOption ? selectedOption.getAttribute('data-placeholder') : "";

    if (isRequired === "true") {
        dynamicInputContainer.style.display = 'block';
        if (dynamicInput) {
            dynamicInput.required = true;
            dynamicInput.placeholder = placeholder;
        }
        if (inputLabel) {
            inputLabel.innerHTML = `REQUIRED USER REFERENCE / APPLICATION ID <span class="text-danger">*</span>`;
        }
    } else {
        dynamicInputContainer.style.display = 'none';
        if (dynamicInput) {
            dynamicInput.required = false;
            dynamicInput.value = '';
        }
    }
}