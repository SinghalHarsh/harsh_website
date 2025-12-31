
# Gita Jar Data
# Structure:
# {
#     "emotion_key": {
#         "label": "Emotion Name",
#         "color": "CSS Color Code",
#         "icon": "FontAwesome Icon Class",
#         "verses": [
#             {
#                 "chapter": 2,
#                 "verse": 47,
#                 "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन...",
#                 "hindi": "तेरा कर्म करने में ही अधिकार है...",
#                 "english": "You have a right to perform your prescribed duty..."
#             }
#         ]
#     }
# }

gita_data = {
    "anger": {
        "label": "Anger",
        "color": "#e74c3c", # Red
        "icon": "fa-solid fa-fire",
        "verses": [
            {
                "chapter": 2,
                "verse": 63,
                "sanskrit": "क्रोधाद्भवति सम्मोह: सम्मोहात्स्मृतिविभ्रम:।\nस्मृतिभ्रंशाद् बुद्धिनाशो बुद्धिनाशात्प्रणश्यति।।",
                "hindi": "क्रोध से अत्यंत मूढ़ भाव उत्पन्न हो जाता है, मूढ़ भाव से स्मृति में भ्रम हो जाता है, स्मृति में भ्रम हो जाने से बुद्धि अर्थात ज्ञानशक्ति का नाश हो जाता है और बुद्धि का नाश हो जाने से यह पुरुष अपनी स्थिति से गिर जाता है।",
                "english": "From anger, complete delusion arises, and from delusion bewilderment of memory. When memory is bewildered, intelligence is lost, and when intelligence is lost one falls down again into the material pool."
            },
            {
                "chapter": 16,
                "verse": 21,
                "sanskrit": "त्रिविधं नरकस्येदं द्वारं नाशनमात्मनः।\nकामः क्रोधस्तथा लोभस्तस्मादेतत्त्रयं त्यजेत्।।",
                "hindi": "काम, क्रोध तथा लोभ- ये तीन प्रकार के नरक के द्वार (आत्मा का) नाश करने वाले अर्थात् उसको अधोगति में ले जाने वाले हैं। अतएव इन तीनों को त्याग देना चाहिए।",
                "english": "There are three gates leading to this hell—lust, anger and greed. Every sane man should give these up, for they lead to the degradation of the soul."
            }
        ]
    },
    "fear": {
        "label": "Fear",
        "color": "#2c3e50", # Dark Blue/Grey
        "icon": "fa-solid fa-ghost",
        "verses": [
            {
                "chapter": 2,
                "verse": 40,
                "sanskrit": "नेहाभिक्रमनाशोऽस्ति प्रत्यवायो न विद्यते।\nस्वल्पमप्यस्य धर्मस्य त्रायते महतो भयात्।।",
                "hindi": "इस कर्मयोग में आरम्भ का अर्थात बीज का नाश नहीं है और उलटा फलरूप दोष भी नहीं है, बल्कि इस कर्मयोग रूप धर्म का थोड़ा-सा भी साधन जन्म-मृत्यु रूप महान भय से रक्षा कर लेता है।",
                "english": "In this endeavor there is no loss or diminution, and a little advancement on this path can protect one from the most dangerous type of fear."
            },
             {
                "chapter": 18,
                "verse": 66,
                "sanskrit": "सर्वधर्मान्परित्यज्य मामेकं शरणं व्रज।\nअहं त्वां सर्वपापेभ्यो मोक्षयिष्यामि मा शुचः।।",
                "hindi": "सब धर्मों को त्यागकर अर्थात हर आश्रय को त्यागकर केवल एक मेरी शरण में आ जा। मैं तुझे संपूर्ण पापों से मुक्त कर दूँगा, तू शोक मत कर।",
                "english": "Abandon all varieties of religion and just surrender unto Me. I shall deliver you from all sinful reactions. Do not fear."
            }
        ]
    },
    "sadness": {
        "label": "Sadness",
        "color": "#7f8c8d", # Grey
        "icon": "fa-solid fa-cloud-rain",
        "verses": [
            {
                "chapter": 2,
                "verse": 13,
                "sanskrit": "देहिनोऽस्मिन्यथा देहे कौमारं यौवनं जरा।\nतथा देहान्तरप्राप्तिर्धीरस्तत्र न मुह्यति।।",
                "hindi": "जैसे जीवात्मा की इस देह में बालकपन, जवानी और वृद्धावस्था होती है, वैसे ही अन्य शरीर की प्राप्ति होती है; उस विषय में धीर पुरुष मोहित नहीं होता।",
                "english": "As the embodied soul continuously passes, in this body, from boyhood to youth to old age, the soul similarly passes into another body at death. A sober person is not bewildered by such a change."
            },
            {
                "chapter": 2,
                "verse": 27,
                "sanskrit": "जातस्य हि ध्रुवो मृत्युर्ध्रुवं जन्म मृतस्य च।\nतस्मादपरिहार्येऽर्थे न त्वं शोचितुमर्हसि।।",
                "hindi": "क्योंकि पैदा हुए की मृत्यु निश्चित है और मरे हुए का जन्म निश्चित है; इससे इस बिना उपाय वाले विषय में तू शोक करने के योग्य नहीं है।",
                "english": "One who has taken his birth is sure to die, and after death one is sure to take birth again. Therefore, in the unavoidable discharge of your duty, you should not lament."
            }
        ]
    },
    "confusion": {
        "label": "Confusion",
        "color": "#8e44ad", # Purple
        "icon": "fa-solid fa-question",
        "verses": [
            {
                "chapter": 2,
                "verse": 7,
                "sanskrit": "कार्पण्यदोषोपहतस्वभावः\nपृच्छामि त्वां धर्मसम्मूढचेताः।\nयच्छ्रेयः स्यान्निश्चितं ब्रूहि तन्मे\nशिष्यस्तेऽहं शाधि मां त्वां प्रपन्नम्।।",
                "hindi": "कायरता रूप दोष से उपहत हुए स्वभाव वाला तथा धर्म के विषय में मोहित चित्त वाला मैं आपसे पूछता हूँ कि जो साधन निश्चित कल्याणकारक हो, वह मेरे लिए कहिए। मैं आपका शिष्य हूँ, इसलिए आपके शरण हुए मुझको शिक्षा दीजिए।",
                "english": "Now I am confused about my duty and have lost all composure because of miserly weakness. In this condition I am asking You to tell me for certain what is best for me. I am Your disciple, and a soul surrendered unto You. Please instruct me."
            }
        ]
    },
    "envy": {
        "label": "Envy",
        "color": "#27ae60", # Green
        "icon": "fa-solid fa-eye",
        "verses": [
            {
                "chapter": 12,
                "verse": 13,
                "sanskrit": "अद्वेष्टा सर्वभूतानां मैत्र: करुण एव च।\nनिर्ममो निरहङ्कार: समदुःखसुख: क्षमी।।",
                "hindi": "जो सब भूतों में द्वेष भाव से रहित, स्वार्थ रहित सबका प्रेमी और हेतु रहित दयालु है तथा ममता से रहित, अहंकार से रहित, सुख-दुःखों की प्राप्ति में सम और क्षमावान है...",
                "english": "One who is not envious but is a kind friend to all living entities, who does not think himself a proprietor and is free from false ego, who is equal in both happiness and distress, who is tolerant..."
            }
        ]
    },
    "pride": {
        "label": "Pride",
        "color": "#d35400", # Dark Orange
        "icon": "fa-solid fa-crown",
        "verses": [
            {
                "chapter": 16,
                "verse": 4,
                "sanskrit": "दम्भो दर्पोऽभिमानश्च क्रोधः पारुष्यमेव च।\nअज्ञानं चाभिजातस्य पार्थ सम्पदमासुरीम्।।",
                "hindi": "हे पार्थ! दम्भ, घमंड, अभिमान, क्रोध, कठोरता और अज्ञान भी - ये सब आसुरी सम्पदा को लेकर उत्पन्न हुए पुरुष के लक्षण हैं।",
                "english": "Pride, arrogance, conceit, anger, harshness and ignorance—these qualities belong to those of demoniac nature, O son of Pṛthā."
            }
        ]
    },
    "lust": {
        "label": "Lust/Desire",
        "color": "#e84393", # Pink
        "icon": "fa-solid fa-heart",
        "verses": [
            {
                "chapter": 2,
                "verse": 62,
                "sanskrit": "ध्यायतो विषयान्पुंस: सङ्गस्तेषूपजायते।\nसङ्गात्सञ्जायते काम: कामात्क्रोधोऽभिजायते।।",
                "hindi": "विषयों का चिन्तन करने वाले पुरुष की उन विषयों में आसक्ति हो जाती है, आसक्ति से उन विषयों की कामना उत्पन्न होती है और कामना में विघ्न पड़ने से क्रोध उत्पन्न होता है।",
                "english": "While contemplating the objects of the senses, a person develops attachment for them, and from such attachment lust develops, and from lust anger arises."
            }
        ]
    },
    "peace": {
        "label": "Peace",
        "color": "#f1c40f", # Yellow
        "icon": "fa-solid fa-dove",
        "verses": [
            {
                "chapter": 2,
                "verse": 71,
                "sanskrit": "विहाय कामान्य: सर्वान्पुमांश्चरति नि:स्पृह:।\nनिर्ममो निरहङ्कार: स शान्तिमधिगच्छति।।",
                "hindi": "जो पुरुष संपूर्ण कामनाओं को त्यागकर ममतारहित, अहंकाररहित और स्पृहारहित होकर विचरता है, वही शांति को प्राप्त होता है।",
                "english": "A person who has given up all desires for sense gratification, who lives free from desires, who has given up all sense of proprietorship and is devoid of false ego—he alone can attain real peace."
            },
            {
                "chapter": 6,
                "verse": 7,
                "sanskrit": "जितात्मनः प्रशान्तस्य परमात्मा समाहितः।\nशीतोष्णसुखदुःखेषु तथा मानापमानयोः।।",
                "hindi": "जिसने मन-इन्द्रियों सहित शरीर को जीत लिया है, उस प्रशांत परमात्मा में एकीभाव से स्थित पुरुष के लिए सर्दी-गर्मी, सुख-दुःख तथा मान-अपमान - ये सब समान हैं।",
                "english": "For one who has conquered the mind, the Supersoul is already reached, for he has attained tranquility. To such a man happiness and distress, heat and cold, honor and dishonor are all the same."
            }
        ]
    }
}
