// NyayaSetu Bot — Hardcoded Legal Q&A Database
// See requirements for structure and content

const LEGAL_QA = {
	// ARREST & POLICE RIGHTS
	arrest_rights: {
		triggers: ['arrested','arrest','detain','detention','custody','lock up',
							 'taken by police','police took me','held by police'],
		answer: `If you are or have been arrested, you have these rights under 
the Indian Constitution and CrPC:

<strong>1. Right to be informed of grounds (Article 22(1))</strong>
Police MUST tell you the reason for your arrest immediately. 
They cannot say "we'll tell you later."

<strong>2. Right to a lawyer (Article 22(1))</strong>
You can consult a lawyer of your choice the moment you are arrested. 
If you cannot afford one, the state must provide one free under 
the Legal Services Authorities Act 1987.

<strong>3. Right to inform family (Section 50A CrPC)</strong>
Police must inform one person of your choice — family member or friend — 
about your arrest and where you are being held.

<strong>4. Right to be produced before a Magistrate within 24 hours 
(Article 22(2) + Section 57 CrPC)</strong>
Police CANNOT hold you beyond 24 hours without producing you before 
a Magistrate. Travel time is excluded from this count.

<strong>5. Right against self-incrimination (Article 20(3))</strong>
You cannot be forced to be a witness against yourself. 
You do not have to answer questions that incriminate you.

<strong>6. Right against illegal search (Section 100 CrPC)</strong>
If police search your home, they must have a warrant (unless it is 
a cognizable offence). Two independent witnesses must be present.

<strong>What police CANNOT do:</strong>
- Torture, beat, or use third-degree methods (violates Article 21)
- Arrest a woman after sunset and before sunrise except in 
	exceptional circumstances with female officer present
- Deny you access to a lawyer
- Keep you beyond 24 hours without magistrate remand

<strong>Immediate steps:</strong>
1. Ask the officer their name and badge number
2. Note the police station name
3. Call a family member or lawyer immediately
4. If ill-treated, file complaint with State Human Rights Commission`,
		confidence: 'high',
		source: 'Constitution of India — Articles 20, 21, 22; CrPC Sections 41, 50, 50A, 57, 100',
		chips: ['Generate my Arrest Rights Card','What if police beat me?',
						'How do I file a complaint against police?','What is anticipatory bail?']
	}
};
};

export default LEGAL_QA;