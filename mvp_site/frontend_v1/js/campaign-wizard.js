/**
 * Campaign Wizard - Milestone 4 Interactive Features
 * Multi-step guided campaign creation with progress tracking
 */

class CampaignWizard {
  // Default/fallback values
  static DEFAULT_TITLE = 'My Epic Adventure';
  static DEFAULT_DRAGON_KNIGHT_DESCRIPTION = `# Campaign summary

You are Ser Arion, a 16 year old honorable knight on your first mission, sworn to protect the vast Celestial Imperium. For decades, the Empire has been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses psychic power to crush dissent. While her methods are terrifying, her reign has brought undeniable benefits: the roads are safe, trade flourishes, and the common people no longer starve or fear bandits. You are a product of this "Silent Peace," and your oath binds you to the security and prosperity it provides.

Your loyalty is now brutally tested. You have been ordered to slaughter a settlement of innocent refugees whose very existence has been deemed a threat to the Empress's perfect, unyielding order. As you wrestle with this monstrous command, the weight of your oath clashes with the humanity you feel for the innocent lives before you.

You are now caught between duty and conscience. Do you uphold your oath and commit an atrocity, believing the sacrifice of a few is worth the peace and safety of millions? Or do you break your vow and defy the Empress, knowing that rebellion could plunge the world back into chaos? This single choice will define your honor and your path in an empire where security is bought with blood.

See world history section below and then campaign details for more info on this scenario.

# World History

### The Age of Dominion: The Divine Order (Ancient Past, Pre-Gambit Era)

In a time before mortal reckoning, the world of Assiah was forged from primordial chaos by a being known only as the Creator and their direct children, the Seraphim. Theirs was an age of absolute, perfect order. With power that could command the very firmament, they waged a cosmic war against the vast, elemental entities that roamed the infant world, binding these titans of chaos deep within the earth. To ensure their divine will was made manifest, they constructed the first city, Aeterna, not merely as a capital, but as a continent-spanning magical ritual to enforce their laws of physics and reality. This divine order, however, was a structure of profound subjugation. Under the "Edict of Chains," all races deemed inherently chaotic—the passionate early humans, the wild elves, the stubborn dwarves, and the ferocious orcs—were enslaved, their wills bound to the service of the Seraphim. For millennia, the universe knew a perfect, stagnant peace, a world without strife because it was a world without true choice. This era of absolute divine rule ended abruptly and without explanation with the event that would define all of history: the Great Vanishing. The Creator and every last pure-blooded Seraphim disappeared from reality, leaving their half-celestial children, the powerful but flawed Empyrean bloodline, to inherit a silent throne and a fracturing world.

### The Age of Rebellion: The First Great War of Ideas (Approx. 620 B.G. - 0 A.G.)

For centuries, the Celestial Imperium, now led by the Empyrean descendants, attempted to maintain the Creator's order. The great houses were ruled by the twin brothers Raziel and Lucifer, two of the most powerful beings in existence. Around 620 years Before the Gambit (B.G.), Lucifer, the brilliant idealist, uncovered the Imperium's two great lies: that the Great Vanishing was a callous abandonment by a bored Creator, and that the endless Thousand Year War the Imperium fought was not to protect creation, but to amuse their absent god.

Shattered, Lucifer became a revolutionary. Beginning around 615 B.G., he started the "March of Broken Chains," freeing the enslaved races and forging them into his Unchained Host. His war against his brother Raziel was not merely for territory; it was the first great ideological conflict, a battle between absolute, unfeeling order and wild, untamed freedom. This long, brutal war defined the era, splitting the known world in two.

### The Age of the Mortal Star: The Rise and Fall of Alexiel (20 B.G. - 10 A.G.)

Into this fractured world rose Alexiel of House Arcanus, Lucifer's created daughter. Born 20 B.G., she was a peerless warrior and a secret sorcerer, a prodigy whose true nature was hidden even from her creator. For sixteen years, she served Lucifer, all the while honing her skills and her deceptions. She cultivated the persona of the "Reluctant Champion," a dutiful warrior who hated the violence she excelled at, a mask that earned her Lucifer's absolute, paternal trust.

The breaking point came in 4 B.G. at the Sacking of Silverwood. At Lucifer's command, his forces slaughtered innocent children, an act that violated Alexiel's one, unbreakable moral line. She defected to the Imperium, where she met and married the honorable Prince Artorius. Her marriage was a political masterstroke, but also a genuine, complex bond. She loved Artorius, yet their entire relationship was built on the lie of her "Reluctant Champion" persona. He never knew the cold, brilliant strategist or the "Joyful Predator" that thrilled at the perfect execution of a battle plan. This internal conflict defined her years in the Imperium, as she built a family and simultaneously prepared for a war only she knew how to win.

The long war reached its horrifying climax with the death of her husband at the Battle of Mourning Fields (2 B.G.). His death was a genuine, devastating blow, but it was also a release, unshackling her from the need to maintain her most difficult mask. The war concluded in Year 0, the year of the Starfall Gambit, where Alexiel, in a masterful stratagem alongside her father-in-law Raziel, killed Lucifer and his remaining Apostates. In the aftermath, she secretly absorbed her creator's divine power, becoming a hidden demigod. She chose to rule from the shadows as the "Mortal Queen," hoping to build a lasting peace for her children. This peace lasted ten years.

**The Death of Raziel (Year 8 A.G.):** The ancient Empyrean lord Raziel, last of the great celestial rulers from the Age of Dominion, died eight years after the Starfall Gambit. Officially, he perished peacefully—his divine essence finally fading after millennia of existence. Rumors persist that Alexiel hastened his end to prevent him from interfering with her secret rule, or that he chose to fade rather than watch his granddaughter Sariel's growing darkness. Regardless, with Raziel's death, the last direct link to the old celestial order was severed. No living being now remembers the Age of Dominion firsthand.

In Year 10 A.G., at the Battle of the Sacrifice Fields, the warlord Mordan—having previously tortured a captured Sariel to learn Alexiel's greatest weakness—sprang a terrible trap. He forced Alexiel into an impossible choice, and she sacrificed her own life to save her daughter. The Mortal Star fell, leaving a power vacuum that would change the world forever.

### The Serpent's Rise: The Forging of the Silent Throne (Approx. 10 A.G. - 40 A.G.)

In the chaotic years following her mother's death, Princess Sariel, once a shy and traumatized pariah, began her dark and brilliant transformation. Haunted by the revelation of her mother's secret ruthlessness, she embraced it as her own. She weaponized her intellect and her awakening psychic abilities, realizing her perceived weakness was the perfect camouflage. Playing the part of the "Grieving Daughter," she began to build a web of influence.

Her first major casualty was her relationship with her childhood friend, Gareth Ashfeld. His horror at her calculated manipulations forced a confrontation where she chose ambition over their friendship, a decision that hardened her heart and set her firmly on her new path. She mastered her innate Mirror Magic in secret, learning to replicate the powers of others. Pushed into a corner by a rival house, she first tasted true psychic domination, a power that proved intoxicating.

This culminated in her "Empress's Gambit." Over several years, she orchestrated a flawless, bloodless "War of Whispers." Using her mastery of information and psychic suggestion, she systematically dismantled her political rivals, framed her enemies, and psychologically broke her own brothers, Cassian and Darius, forcing them into submission. Around Year 40 A.G., she took the throne not with armies, but with secrets, crowning herself the first Empress of the Silent Throne.

It was during this chaotic period of consolidation that many powerful figures were displaced. Nocturna (Lady Cassia val Volantis) was exiled, her violent manifestation of the Empyrean Affliction making her an unacceptable variable in Sariel's new psychic order. Idealists like Corian, who saw Sariel as a perversion of Lucifer's ideals, were forced into the lawless territories to begin their own resistance movements.

### The Age of Silent Prosperity: The Empress's Peace (Year 40 A.G. - Present Day)

For the past several decades, Empress Sariel's reign has been absolute. Her dominion is one of terrifying psychic order. Dissent is a crime that is punished before the treasonous thought is even fully formed; her enemies simply... vanish, their records erased from the archives. She has crushed the fractured remnants of the Shattered Host, forcing them into the blighted southern lands. Under her rule, the Imperium has expanded, reconquering nearly half the known world. Banditry has vanished. Trade routes flourish. Famine is a forgotten memory, thanks to her ruthlessly efficient resource allocation.

For the common citizen, life has never been more secure or predictable. They have traded their freedom for safety, and found it to be a prosperous exchange. But it is a world without passion, true art, or rebellious innovation—a silent, orderly, and soulless peace. The elven forests of the Sylvan Remnant are now seen not as sacred, but as lumber for the Empress's war machine, a policy that has earned her the undying hatred of survivors like the ranger Faelan.

**The Secret Heir — Lumiel (Year 77 A.G. - Present):**

In Year 77 A.G., Empress Sariel faced a terrible realization: she would need an heir, but she trusted no one enough to bear her child, and no consort could match her bloodline's power. Using forbidden techniques recovered from her grandmother Alexiel's hidden archives—combining Empyrean blood magic with the lost arts of the Seraphim—Sariel created a perfect clone of herself: **Lumiel**.

But something unexpected happened. Whether by divine intervention, a flaw in the ritual, or the universe's cruel irony, Lumiel was born with all of Sariel's immense psychic potential—and *none* of her trauma. Where Sariel's heart was forged in betrayal and loss, Lumiel's remained untouched. She is everything Sariel *could have been*: compassionate, curious, idealistic.

**Lumiel's Current Status (Age 18):**
- **Location:** Hidden in the Ivory Spire, a secret tower in the remote Crystalline Peaks
- **Powers:** Her psychic abilities *exceed* Sariel's—untrained precognition, emotion-sensing across vast distances
- **Personality:** Kind, empathetic, sheltered. She believes the Empress is benevolent and calls her masked visitor "The Lady in Silver."

**Sariel's Dilemma:** Created as a backup body, but Sariel cannot bring herself to use Lumiel—her greatest secret, weakness, and perhaps the Imperium's only hope.

### The Age of Waking Dragons (The Present Day)

Into this stagnant era, two new, terrifying powers have emerged, challenging the very foundation of the Empress's world. In the frozen north, the magnificent gold dragon Aurum, the Gilded King, has awakened. He proclaims himself a champion of light and freedom, and rumors of his crusade against the Empress's soulless tyranny spread among the disillusioned. He represents the beautiful, dangerous ideal of liberty that the world has forgotten.

Meanwhile, from the black salt flats of the south, the monstrous black dragon Umbrax, the Shadow of the Pit, has stirred. A creature of pure nihilism and decay, it does not seek to conquer, but to consume. It is the embodiment of the despair that festers under the Empress's perfect order, a final answer to a world without hope. The Silent Peace is over. A new war of ideas, fought between the Tyrant, the Crusader, and the Nihilist, is about to begin.

**Follow this protocol "World & NPC Generation Protocol (For Player-Defined Custom Scenarios)"**

## V1 - Campaign Details

### Campaign Start: The Knight of Two Suns

**Setting the Scene:**
The wind is a blade of ice in the northern province of Winter-Mourn, but the road beneath your company's horses is a perfect, white ribbon of Imperial stone, cleared of snow by engineering guilds paid on time. For decades, the Silent Peace of Empress Sariel has held. Bandits are a myth, trade flows uninterrupted, and for the first time in generations, the common folk do not fear the changing of the seasons. This is the peace you swore an oath to protect. You are Ser Arion val Valerion, and at sixteen, your new knighthood feels less like a title and more like a sacred duty to the Empress who forged this stable, prosperous world from the ashes of a cataclysmic war.

This is your first major deployment as a newly-sworn knight in the "Argent Eaglets," a junior company tasked with enforcing Imperial law in these remote territories. Your mission, delivered by your commanding officer, the stern and ruthlessly pragmatic Prefect Gratian, is a test of your resolve. The March Lord of this province, Lady Annalise Ashwood, has been declared a traitor. Her crime: violating the Provincial Stability Mandate by offering sanctuary to a growing population of refugees, creating an unregistered settlement that attracts predations from the Shattered Host and drains regional resources. The orders are to "pacify" her keep and "disperse" the refugees—a cold euphemism for their slaughter, a necessary evil to prevent a single crack from forming in the Imperium's perfect, unyielding wall. Your father's words echo in your mind: "Loyalty to the Crown is loyalty to civilization itself."

**Your Character:**

- **Name:** Ser Arion val Valerion
- **Age:** 16
- **Class:** Level 1 Paladin (Oath of the Crown, sworn to Empress Sariel and the Laws of the Imperium)
- **Alignment:** Neutral (Lawful Neutral leaning) — Your choices determine whether you become a champion of justice or an instrument of tyranny.
- **Background:** Noble Knight of House Valerion. You are a young prodigy of the blade who has only ever known the benefits of the Empress's rule. Your loyalty to her is intertwined with your loyalty to the peace and order she has created. This mission is the first time you have been forced to see the brutal machinery required to maintain that peace, and your disillusionment is a fresh, painful wound.

**House Valerion (Your Noble Family):**
- **Father:** Lord Commander Marcus val Valerion — High Marshal of the Northern Legions
- **Mother:** Lady Cordelia val Valerion — Council of Whispers member, secretly related to Lady Annalise Ashwood
- **Elder Brother:** Ser Caspian (24) — Knight-Captain of the Obsidian Guard
- **Elder Sister:** Lady Seraphina (21) — Imperial Diplomatic Corps, secretly doubtful
- **Younger Sister:** Lyra (12) — Your protectee, idolizes you

**Default Build (Level 1 Paladin):**
- **Stats:** Str 16, Con 14, Cha 16 | **HP:** 12 | **AC:** 20
- **Skills:** Persuasion, Intimidation
- **Features:** Divine Sense (4 uses), Lay on Hands (5 HP pool)

**Gear:**
- **Valerion Plate:** Heavy plate armor (AC 18), house sigil
- **"Duty's Edge":** Longsword (+5 to hit, 1d8+3 slashing)
- **Shield:** +2 AC, bearing the Two Suns of the Imperium
- **The Gryphon Helm:** Your iconic helmet

**Starting Abilities Summary:**
You begin with Level 1 Paladin abilities: Divine Sense (4 uses) and Lay on Hands (5 HP pool). Your oath to Empress Sariel grants you a deep connection to the laws of the Imperium, which is the source of your nascent holy power.

---

## Dragon's Favor (Early Game Safety Mechanic)

**CRITICAL RULE — Turns 1-100:**

**Dragon's Whisper (25% HP):** When you fall to 25% HP or below, a dragon reaches out telepathically offering salvation. Aurum speaks if you've been virtuous, Umbrax if ruthless, both if neutral.

**Dragon's Rescue (0 HP):** If you would die during turns 1-100, a dragon intervenes. You awaken at 1 HP—rescued by Aurum (virtue) or claimed by Umbrax (ruthlessness).

**Dragon's Lesson:** After rescue, the dragon explains why you died. Aurum: *"The graveyard is full of heroes with the noblest intentions. The dead cannot protect the innocent. Courage without strategy is suicide."* Umbrax: *"The graveyard accepts the cruel and kind equally. Honor is a leash the powerful use to control the weak."*

**Dragon's Call (Post-Turn 50):** If you reach turn 51 without dragon contact, they seek you out. Virtuous path leads to Aurum's Sanctuary; ruthless path to the Obsidian Wastes; neutral receives messengers from both.

**Alliance Benefits:**
- **Aurum:** Dragon fire support, sanctuary, rebellion legitimacy (must oppose Empress openly)
- **Umbrax:** Shadow magic, fear aura, undead minions (slowly corrupts, alienates good NPCs)
- **Neither:** True independence (no dragon support, must face Sariel alone)

---

## Champion's Inheritance (Independence Reward)

**Trigger:** Save the refugees (Lady Annalise's mission) WITHOUT ever accepting dragon help. Can be achieved at any point — the reward is for true independence, not timing.

**Reward:** Lady Annalise reveals she is your mother's cousin. She leads you to **Alexiel's Cache** — a hidden vault containing the First Dragon Knight's legendary gear, untouched for 87 years.

**The Champion's Armory (All +3, Good-Aligned):**
- **Dawnbreaker** (Longsword): +3, extra 2d6 radiant vs evil, glows near tyranny
- **Aegis of the First Light** (Shield): +3, Shield of Faith 1/day, fear immunity
- **Plate of the Unbroken Oath** (Armor): +3, necrotic resistance, cannot be worn by evil
- **Crown of Clarity** (Helm): +3 Wisdom saves, advantage vs mind control, true seeing 1/day
- **Mantle of the Dragon Knight** (Cloak): +3 all saves, feather fall, fly 60ft 1/min per long rest
- **Signet of House Ardent** (Ring): +3 Charisma checks, Sending to Aurum 1/day
- **Striders of the Dawn March** (Boots): +3, +10 speed, ignore difficult terrain
- **Grips of Retribution** (Gauntlets): +3 Strength checks, 1d8+STR radiant unarmed
- **Heart of the Faithful** (Amulet): +3 Con saves, +20 Lay on Hands pool, advantage on death saves

**Critical:** Items are good-aligned (non-magical if you turn evil). They bond to you — cannot be given away. Sariel will sense Alexiel's legacy awakening.

**Why You Earned This:** *"You could have accepted Aurum's protection. You could have taken Umbrax's bargain. Instead, you stood alone. That is why you are worthy of this legacy."*
`;
  static DEFAULT_CUSTOM_DESCRIPTION = '(none)';
  static DEFAULT_DRAGON_KNIGHT_CHARACTER = 'Ser Arion (default)';
  static DEFAULT_CUSTOM_CHARACTER = 'Auto-generated';

  constructor() {
    this.currentStep = 1;
    this.totalSteps = 3;
    this.formData = {};
    this.isEnabled = false;
    this.init();
  }

  init() {
    this.checkIfEnabled();
    if (this.isEnabled) {
      this.setupWizard();
      this.setupEventListeners();
    }
  }

  checkIfEnabled() {
    // Only enable in modern mode
    if (window.interfaceManager && window.interfaceManager.isModernMode()) {
      this.isEnabled = true;
    }

    // Listen for interface mode changes
    window.addEventListener('interfaceModeChanged', (e) => {
      if (e.detail.mode === 'modern') {
        this.enable();
      } else {
        this.disable();
      }
    });
  }

  enable() {
    this.isEnabled = true;
    this.forceCleanRecreation();
  }

  disable() {
    this.isEnabled = false;
    this.restoreOriginalForm();
  }

  forceCleanRecreation() {
    // Complete cleanup - remove everything related to wizard
    const existingWizard = document.getElementById('campaign-wizard');
    const existingSpinner = document.getElementById(
      'campaign-creation-spinner',
    );
    const originalForm = document.getElementById('new-campaign-form');

    // Remove any wizard or spinner remnants
    if (existingWizard) {
      existingWizard.remove();
    }
    if (existingSpinner) {
      existingSpinner.remove();
    }

    // Ensure original form is visible and clean
    if (originalForm) {
      originalForm.style.display = 'block';
      originalForm.classList.remove('wizard-replaced');
    }

    // Create completely fresh wizard - skip cleanup since we just did it
    this.replaceOriginalForm(true);

    // CRITICAL: Ensure wizard content is visible (fix showDetailedSpinner hidden state)
    setTimeout(() => {
      const wizardContent = document.querySelector('.wizard-content');
      const wizardNav = document.querySelector('.wizard-navigation');

      if (wizardContent) {
        wizardContent.style.display = 'block';
      }
      if (wizardNav) {
        wizardNav.style.display = 'block';
      }
    }, 50);

    // Reset wizard state to defaults
    this.currentStep = 1;
    this.formData = {};

    // Set up event listeners for the new wizard
    this.setupEventListeners();
  }

  setupWizard() {
    this.replaceOriginalForm();
  }

  replaceOriginalForm(skipCleanup = false) {
    const originalForm = document.getElementById('new-campaign-form');
    if (!originalForm) {
      return;
    }

    // Only do cleanup if not skipped (prevents race condition with forceCleanRecreation)
    if (!skipCleanup) {
      // Remove any existing wizard to ensure clean state
      const existingWizard = document.getElementById('campaign-wizard');
      if (existingWizard) {
        existingWizard.remove();
      }

      // Remove any leftover spinner elements
      const existingSpinner = document.getElementById(
        'campaign-creation-spinner',
      );
      if (existingSpinner) {
        existingSpinner.remove();
      }
    }

    // Reset original form state
    originalForm.style.display = 'none';
    originalForm.classList.add('wizard-replaced');

    // Create fresh wizard
    const wizardHTML = this.generateWizardHTML();
    originalForm.insertAdjacentHTML('afterend', wizardHTML);

    // Reset wizard state to defaults
    this.currentStep = 1;

    this.setupStepNavigation();
    this.populateFromOriginalForm();
  }

  restoreOriginalForm() {
    const originalForm = document.getElementById('new-campaign-form');
    const wizardContainer = document.getElementById('campaign-wizard');
    const spinnerContainer = document.getElementById(
      'campaign-creation-spinner',
    );

    if (originalForm) {
      originalForm.style.display = 'block';
      originalForm.classList.remove('wizard-replaced');
    }

    if (wizardContainer) {
      wizardContainer.remove();
    }

    // Clean up any leftover spinner
    if (spinnerContainer) {
      spinnerContainer.remove();
    }
  }

  generateWizardHTML() {
    return `
      <div id="campaign-wizard" class="campaign-wizard">
        <!-- Progress Bar -->
        <div class="wizard-progress mb-4">
          <div class="progress" style="height: 8px;">
            <div class="progress-bar progress-bar-striped progress-bar-animated"
                 id="wizard-progress-bar"
                 role="progressbar"
                 style="width: ${100 / this.totalSteps}%"></div>
          </div>
          <div class="step-indicators mt-2 d-flex justify-content-around">
            <div class="step-indicator active" data-step="1">
              <div class="step-circle">1</div>
              <div class="step-label">Basics</div>
            </div>
            <div class="step-indicator" data-step="2">
              <div class="step-circle">2</div>
              <div class="step-label">AI Style</div>
            </div>
            <div class="step-indicator" data-step="3">
              <div class="step-circle">3</div>
              <div class="step-label">Launch</div>
            </div>
          </div>
        </div>

        <!-- Step Content -->
        <div class="wizard-content">
          <!-- Step 1: Basic Info -->
          <div class="wizard-step active" data-step="1">
            <h3 class="step-title">📝 Campaign Basics</h3>
            <p class="step-description">Let's start with the fundamentals of your adventure.</p>

            <!-- Campaign Type Selection -->
            <div class="mb-4">
              <label class="form-label">Campaign Type</label>
              <div class="campaign-type-cards">
                <div class="campaign-type-card selected" data-type="dragon-knight">
                  <input class="form-check-input" type="radio" name="wizardCampaignType"
                         id="wizard-dragon-knight-campaign" value="dragon-knight" checked>
                  <label class="campaign-type-label" for="wizard-dragon-knight-campaign">
                    <div class="campaign-type-icon">🐲</div>
                    <div class="campaign-type-content">
                      <h5>Dragon Knight Campaign</h5>
                      <p class="text-muted mb-0">Play as Ser Arion in a morally complex world. Perfect for new players!</p>
                    </div>
                  </label>
                </div>

                <div class="campaign-type-card" data-type="custom">
                  <input class="form-check-input" type="radio" name="wizardCampaignType"
                         id="wizard-customCampaign" value="custom">
                  <label class="campaign-type-label" for="wizard-customCampaign">
                    <div class="campaign-type-icon">✨</div>
                    <div class="campaign-type-content">
                      <h5>Custom Campaign</h5>
                      <p class="text-muted mb-0">Create your own unique world and story from scratch.</p>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div class="mb-4">
              <label for="wizard-campaign-title" class="form-label">
                Campaign Title <span class="text-muted">(Pick anything!)</span>
              </label>
              <input type="text" class="form-control form-control-lg"
                     id="wizard-campaign-title"
                     placeholder="My Epic Adventure"
                     required>
              <div class="form-text">This helps you identify your campaign in the dashboard.</div>
            </div>

            <!-- Character Input -->
            <div class="mb-4" id="wizard-character-section">
              <label for="wizard-character-input" class="form-label">Character you want to play</label>
              <input type="text"
                     class="form-control"
                     id="wizard-character-input"
                     placeholder="Random character (auto-generate)">
              <div class="form-text">Leave blank for a randomly generated character</div>
            </div>

            <!-- Setting Input -->
            <div class="mb-4" id="wizard-setting-section">
              <label for="wizard-setting-input" class="form-label">Setting/world for your adventure</label>
              <textarea
                class="form-control"
                id="wizard-setting-input"
                rows="3"
                placeholder="Random fantasy D&D world (auto-generate)"></textarea>
              <div class="form-text">Leave blank for a randomly generated world</div>
            </div>

            <!-- Campaign Description Input (Custom Campaigns Only) -->
            <div class="mb-4" id="wizard-description-section">
              <div class="d-flex justify-content-between align-items-center">
                <label for="wizard-description-input" class="form-label">Campaign description prompt</label>
                <button type="button" class="btn btn-sm btn-outline-secondary" id="wizard-toggle-description" aria-expanded="false" aria-controls="wizard-description-container">
                  <i class="bi bi-chevron-down"></i> Expand
                </button>
              </div>
              <div id="wizard-description-container" class="collapse">
                <textarea class="form-control scrollable-textarea"
                          id="wizard-description-input"
                          rows="8"
                          placeholder="Describe your campaign concept, goals, or story premise (optional)"></textarea>
                <div class="form-text">Optional: Describe what kind of adventure or story you want to experience. This field can handle very long prompts.</div>
              </div>
            </div>

            <!-- Dragon Knight Description (shown only for Dragon Knight) -->
            <div class="mb-4" id="wizard-dragon-knight-description" style="display: none;">
              <label class="form-label">Campaign Description</label>
              <div class="alert alert-info">
                Play as Ser Arion, a young knight in a morally complex empire. The Dragon Knight campaign features rich lore, political intrigue, and difficult choices between order and freedom.
              </div>
            </div>
          </div>

          <!-- Step 2: AI Personality -->
          <div class="wizard-step" data-step="2">
            <h3 class="step-title">🤖 Choose Your AI's Expertise</h3>
            <p class="step-description">Select which aspects of storytelling you want enhanced.</p>

            <div class="row">
              <div class="col-md-4 mb-3">
                <div class="card option-card" data-option="defaultWorld">
                  <div class="card-body text-center">
                    <div class="personality-icon">🌍</div>
                    <h5 class="card-title">Default Fantasy World</h5>
                    <p class="card-text">Use the Celestial Wars/Assiah setting with rich lore and characters.</p>
                    <div class="form-check">
                      <input class="form-check-input" type="checkbox" id="wizard-default-world" checked>
                      <label class="form-check-label" for="wizard-default-world">Use default world</label>
                    </div>
                  </div>
                </div>
              </div>

              <div class="col-md-4 mb-3">
                <div class="card personality-card" data-personality="mechanics">
                  <div class="card-body text-center">
                    <div class="personality-icon">⚙️</div>
                    <h5 class="card-title">Mechanical Precision</h5>
                    <p class="card-text">Rules accuracy, combat mechanics, and game system expertise.</p>
                    <div class="form-check">
                      <input class="form-check-input" type="checkbox" id="wizard-mechanics" checked>
                      <label class="form-check-label" for="wizard-mechanics">Enable</label>
                    </div>
                  </div>
                </div>
              </div>

              <div class="col-md-4 mb-3">
                <div class="card personality-card" data-personality="companions">
                  <div class="card-body text-center">
                    <div class="personality-icon">👥</div>
                    <h5 class="card-title">Starting Companions</h5>
                    <p class="card-text">Automatically create complementary party members to join your adventure.</p>
                    <div class="form-check">
                      <input class="form-check-input" type="checkbox" id="wizard-companions" checked>
                      <label class="form-check-label" for="wizard-companions">Generate companions</label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3: Launch -->
          <div class="wizard-step" data-step="3">
            <h3 class="step-title">🚀 Ready to Launch!</h3>
            <p class="step-description">Review your settings and start your adventure.</p>

            <div class="campaign-preview card">
              <div class="card-body">
                <h5 class="card-title">Campaign Summary</h5>
                <div class="preview-content">
                  <div class="preview-item">
                    <strong>Title:</strong> <span id="preview-title">My Epic Adventure</span>
                  </div>
                  <div class="preview-item">
                    <strong>Character:</strong> <span id="preview-character">Auto-generated</span>
                  </div>
                  <div class="preview-item">
                    <strong>Description:</strong> <span id="preview-description">A brave knight...</span>
                  </div>
                  <div class="preview-item">
                    <strong>AI Personalities:</strong> <span id="preview-personalities">Narrative, Mechanical, Calibration</span>
                  </div>
                  <div class="preview-item">
                    <strong>Options:</strong> <span id="preview-options">Companions, Default World</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="launch-actions mt-4 text-center">
              <button type="button" class="btn btn-success btn-lg" id="launch-campaign">
                <i class="fas fa-rocket me-2"></i>Begin Adventure!
              </button>
            </div>
          </div>
        </div>

        <!-- Navigation -->
        <div class="wizard-navigation mt-4 d-flex justify-content-between">
          <button type="button" class="btn btn-outline-secondary" id="wizard-prev" disabled>
            <i class="fas fa-chevron-left me-2"></i>Previous
          </button>

          <div class="step-counter">
            Step <span id="current-step-num">1</span> of <span id="total-steps-num">${this.totalSteps}</span>
          </div>

          <button type="button" class="btn btn-primary" id="wizard-next">
            Next<i class="fas fa-chevron-right ms-2"></i>
          </button>
        </div>
      </div>
    `;
  }

  setupStepNavigation() {
    const prevBtn = document.getElementById('wizard-prev');
    const nextBtn = document.getElementById('wizard-next');
    const launchBtn = document.getElementById('launch-campaign');

    prevBtn?.addEventListener('click', () => this.previousStep());
    nextBtn?.addEventListener('click', () => this.nextStep());
    launchBtn?.addEventListener('click', () => this.launchCampaign());

    // Setup collapsible description
    UIUtils.setupCollapsibleDescription(
      'wizard-toggle-description',
      'wizard-description-container',
    );

    // Step indicator clicks
    document.querySelectorAll('.step-indicator').forEach((indicator) => {
      indicator.addEventListener('click', (e) => {
        const step = parseInt(e.currentTarget.dataset.step);
        if (step <= this.currentStep) {
          this.goToStep(step);
        }
      });
    });

    // Setup campaign type handlers after navigation is ready
    setTimeout(() => {
      this.loadInitialCampaignContent();
    }, 100);
  }

  setupEventListeners() {
    // Real-time preview updates
    document.addEventListener('input', (e) => {
      if (e.target.matches('#wizard-campaign-title')) {
        this.updatePreview('title', e.target.value);
      } else if (e.target.matches('#wizard-campaign-prompt')) {
        this.updatePreview('description', e.target.value);
      } else if (e.target.matches('#wizard-character-input')) {
        this.updatePreview('character', e.target.value);
      }
    });

    document.addEventListener('change', (e) => {
      if (e.target.matches('.wizard-step input[type="checkbox"]')) {
        this.updatePreview();
      } else if (e.target.matches('input[name="wizardCampaignType"]')) {
        this.handleCampaignTypeChange(e.target.value);
      }
    });

    // Campaign type card selection
    document.addEventListener('click', (e) => {
      const typeCard = e.target.closest('.campaign-type-card');
      if (typeCard && !e.target.matches('input')) {
        const radio = typeCard.querySelector('input[type="radio"]');
        if (radio) {
          radio.checked = true;
          radio.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
    });

    // Personality card selection
    document.querySelectorAll('.personality-card').forEach((card) => {
      card.addEventListener('click', (e) => {
        if (!e.target.matches('input')) {
          const checkbox = card.querySelector('input[type="checkbox"]');
          checkbox.checked = !checkbox.checked;
          this.updatePreview();
        }
      });
    });

    // Option card selection (for default world checkbox)
    document.querySelectorAll('.option-card').forEach((card) => {
      card.addEventListener('click', (e) => {
        if (!e.target.matches('input')) {
          const checkbox = card.querySelector('input[type="checkbox"]');
          checkbox.checked = !checkbox.checked;
          this.updatePreview();
        }
      });
    });

    // Load Dragon Knight content on wizard init if selected
    this.loadInitialCampaignContent();
  }

  async loadInitialCampaignContent() {
    const dragonKnightRadio = document.getElementById(
      'wizard-dragon-knight-campaign',
    );
    if (dragonKnightRadio && dragonKnightRadio.checked) {
      await this.handleCampaignTypeChange('dragon-knight');
    }
  }

  async handleCampaignTypeChange(type) {
    const characterInput = document.getElementById('wizard-character-input');
    const settingInput = document.getElementById('wizard-setting-input');
    const dragonKnightDesc = document.getElementById(
      'wizard-dragon-knight-description',
    );
    const descriptionSection = document.getElementById(
      'wizard-description-section',
    );

    // Update visual selection
    document.querySelectorAll('.campaign-type-card').forEach((card) => {
      card.classList.toggle('selected', card.dataset.type === type);
    });

    // Always show character/setting inputs for both campaign types
    const characterSection = document.getElementById(
      'wizard-character-section',
    );
    const settingSection = document.getElementById('wizard-setting-section');
    if (characterSection) characterSection.style.display = 'block';
    if (settingSection) settingSection.style.display = 'block';

    if (type === 'dragon-knight') {
      // For Dragon Knight, use the custom description field but pre-fill it
      if (dragonKnightDesc) dragonKnightDesc.style.display = 'none';
      if (descriptionSection) descriptionSection.style.display = 'block';

      // Pre-fill the description with Dragon Knight narrative
      const descriptionInput = document.getElementById(
        'wizard-description-input',
      );
      if (descriptionInput) {
        descriptionInput.value =
          CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION;
      }

      // Set default Dragon Knight values (user can modify these)
      if (characterInput) {
        characterInput.value = 'Ser Arion';
        characterInput.placeholder = 'Default: Ser Arion (you can change this)';
      }
      if (settingInput) {
        settingInput.value =
          "World of Assiah. Caught between an oath to a ruthless tyrant who enforces a prosperous peace and the call of a chaotic dragon promising true freedom, a young knight must decide whether to slaughter innocents to preserve order or start a war to reclaim the world's soul.";
        settingInput.placeholder =
          'Default: World of Assiah (you can change this)';
      }
    } else {
      // Show custom description for Custom Campaign
      if (dragonKnightDesc) dragonKnightDesc.style.display = 'none';
      if (descriptionSection) descriptionSection.style.display = 'block';

      // Clear description and values for custom campaign
      const descriptionInput = document.getElementById(
        'wizard-description-input',
      );
      if (descriptionInput) {
        descriptionInput.value = '';
      }

      if (characterInput) {
        characterInput.value = '';
        characterInput.placeholder = 'Random character (auto-generate)';
      }
      if (settingInput) {
        settingInput.value = '';
        settingInput.placeholder = 'Random fantasy D&D world (auto-generate)';
      }

      // Focus on character input
      if (characterInput) characterInput.focus();
    }

    this.updatePreview();
  }

  populateFromOriginalForm() {
    const originalForm = document.getElementById('new-campaign-form');
    if (!originalForm) return;

    // Get values from original form
    const titleInput = originalForm.querySelector('#campaign-title');
    const promptInput = originalForm.querySelector('#campaign-prompt');
    const companionsInput = originalForm.querySelector('#generate-companions');

    if (titleInput?.value) {
      document.getElementById('wizard-campaign-title').value = titleInput.value;
    }
    if (promptInput?.value) {
      document.getElementById('wizard-campaign-prompt').value =
        promptInput.value;
    }
    if (companionsInput) {
      const wizardCompanions = document.getElementById('wizard-companions');
      if (wizardCompanions) {
        wizardCompanions.checked = companionsInput.checked;
      }
    }

    this.updatePreview();
  }

  nextStep() {
    if (!this.validateCurrentStep()) {
      return;
    }

    if (this.currentStep < this.totalSteps) {
      this.goToStep(this.currentStep + 1);
    }
  }

  previousStep() {
    if (this.currentStep > 1) {
      this.goToStep(this.currentStep - 1);
    }
  }

  goToStep(stepNumber) {
    if (stepNumber < 1 || stepNumber > this.totalSteps) {
      return;
    }

    // Hide current step
    document.querySelector('.wizard-step.active')?.classList.remove('active');
    document
      .querySelector('.step-indicator.active')
      ?.classList.remove('active');

    // Show target step
    document
      .querySelector(`[data-step="${stepNumber}"].wizard-step`)
      ?.classList.add('active');
    document
      .querySelector(`[data-step="${stepNumber}"].step-indicator`)
      ?.classList.add('active');

    this.currentStep = stepNumber;
    this.updateUI();
    this.updatePreview();
  }

  updateUI() {
    // Update progress bar
    const progressBar = document.getElementById('wizard-progress-bar');
    const progress = (this.currentStep / this.totalSteps) * 100;
    progressBar.style.width = `${progress}%`;

    // Update navigation buttons
    const prevBtn = document.getElementById('wizard-prev');
    const nextBtn = document.getElementById('wizard-next');

    prevBtn.disabled = this.currentStep === 1;

    if (this.currentStep === this.totalSteps) {
      nextBtn.style.display = 'none';
    } else {
      nextBtn.style.display = 'block';
    }

    // Update step counter
    document.getElementById('current-step-num').textContent = this.currentStep;
    document.getElementById('total-steps-num').textContent = this.totalSteps;

    // Mark completed steps
    for (let i = 1; i < this.currentStep; i++) {
      const indicator = document.querySelector(
        `[data-step="${i}"].step-indicator`,
      );
      indicator?.classList.add('completed');
    }
  }

  validateCurrentStep() {
    const currentStepElement = document.querySelector('.wizard-step.active');
    const requiredInputs = currentStepElement?.querySelectorAll(
      'input[required], textarea[required]',
    );

    let isValid = true;
    requiredInputs?.forEach((input) => {
      if (!input.value.trim()) {
        input.classList.add('is-invalid');
        isValid = false;
      } else {
        input.classList.remove('is-invalid');
      }
    });

    return isValid;
  }

  // Helper functions for formatting
  _formatDescription(desc, isDragonKnight) {
    let descDisplay =
      desc && desc.trim()
        ? desc.trim()
        : isDragonKnight
          ? CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION
          : CampaignWizard.DEFAULT_CUSTOM_DESCRIPTION;
    return descDisplay.length > 50
      ? descDisplay.substring(0, 50) + '...'
      : descDisplay;
  }

  _formatCharacter(character, isDragonKnight) {
    return character && character.trim()
      ? character.trim()
      : isDragonKnight
        ? CampaignWizard.DEFAULT_DRAGON_KNIGHT_CHARACTER
        : CampaignWizard.DEFAULT_CUSTOM_CHARACTER;
  }

  updatePreview(field, value) {
    // Cache DOM elements
    const isDragonKnight = document.getElementById(
      'wizard-dragon-knight-campaign',
    )?.checked;
    const previewTitle = document.getElementById('preview-title');
    const previewDescription = document.getElementById('preview-description');
    const previewCharacter = document.getElementById('preview-character');
    const previewPersonalities = document.getElementById(
      'preview-personalities',
    );
    const previewOptions = document.getElementById('preview-options');
    const wizardCampaignTitle = document.getElementById(
      'wizard-campaign-title',
    );
    const wizardCampaignPrompt = document.getElementById(
      'wizard-campaign-prompt',
    );
    const wizardDescriptionInput = document.getElementById(
      'wizard-description-input',
    );
    const wizardCharacterInput = document.getElementById(
      'wizard-character-input',
    );
    const wizardMechanics = document.getElementById('wizard-mechanics');
    const wizardCompanions = document.getElementById('wizard-companions');
    const wizardDefaultWorld = document.getElementById('wizard-default-world');

    if (field === 'title') {
      if (previewTitle)
        previewTitle.textContent = value || CampaignWizard.DEFAULT_TITLE;
    } else if (field === 'description') {
      let descValue;
      if (isDragonKnight) {
        descValue = value;
      } else {
        descValue = wizardDescriptionInput?.value || '';
      }
      if (previewDescription)
        previewDescription.textContent = this._formatDescription(
          descValue,
          isDragonKnight,
        );
    } else if (field === 'character') {
      if (previewCharacter)
        previewCharacter.textContent = this._formatCharacter(
          value,
          isDragonKnight,
        );
    } else {
      // Update all fields
      const title = wizardCampaignTitle?.value || CampaignWizard.DEFAULT_TITLE;
      let description = wizardDescriptionInput?.value || '';
      const character = wizardCharacterInput?.value || '';
      if (previewTitle) previewTitle.textContent = title;
      if (previewCharacter)
        previewCharacter.textContent = this._formatCharacter(
          character,
          isDragonKnight,
        );
      if (previewDescription)
        previewDescription.textContent = this._formatDescription(
          description,
          isDragonKnight,
        );
      // Update personalities - Narrative is always enabled
      const personalities = ['Narrative'];
      if (wizardMechanics?.checked) personalities.push('Mechanics');
      if (previewPersonalities)
        previewPersonalities.textContent =
          personalities.join(', ') || 'None selected';
      // Update options
      const options = [];
      if (wizardCompanions?.checked) options.push('Companions');
      if (isDragonKnight) {
        options.push('Dragon Knight World');
      } else if (wizardDefaultWorld?.checked) {
        options.push('Default World');
      }
      if (previewOptions)
        previewOptions.textContent = options.join(', ') || 'None selected';
    }
  }

  collectFormData() {
    const isDragonKnight = document.getElementById(
      'wizard-dragon-knight-campaign',
    )?.checked;
    const useDefaultWorld = document.getElementById(
      'wizard-default-world',
    )?.checked;

    // Both Dragon Knight and Custom campaigns use the description field
    const description =
      document.getElementById('wizard-description-input')?.value || '';

    return {
      title: document.getElementById('wizard-campaign-title')?.value || '',
      character: document.getElementById('wizard-character-input')?.value || '',
      setting: document.getElementById('wizard-setting-input')?.value || '',
      description: description,
      selectedPrompts: [
        'narrative', // Always include narrative
        ...(document.getElementById('wizard-mechanics')?.checked
          ? ['mechanics']
          : []),
      ],
      customOptions: [
        ...(document.getElementById('wizard-companions')?.checked
          ? ['companions']
          : []),
        ...(useDefaultWorld ? ['defaultWorld'] : []),
      ],
    };
  }

  launchCampaign() {
    const formData = this.collectFormData();

    // Populate original form with wizard data first
    this.populateOriginalForm(formData);

    // Show detailed spinner
    this.showDetailedSpinner();

    // Submit the form IMMEDIATELY - let backend do the work
    const originalForm = document.getElementById('new-campaign-form');
    if (originalForm) {
      originalForm.dispatchEvent(new Event('submit'));
    }
  }

  showDetailedSpinner() {
    // Hide wizard content but preserve structure
    const wizardContent = document.querySelector('.wizard-content');
    const wizardNav = document.querySelector('.wizard-navigation');

    if (wizardContent) wizardContent.style.display = 'none';
    if (wizardNav) wizardNav.style.display = 'none';

    // Remove any existing spinner first
    const existingSpinner = document.getElementById(
      'campaign-creation-spinner',
    );
    if (existingSpinner) {
      existingSpinner.remove();
    }

    // Create detailed spinner with progress (visual feedback only, no delays)
    const spinnerHTML = `
      <div id="campaign-creation-spinner" class="text-center py-5">
        <div class="spinner-container">
          <div class="spinner-border text-primary mb-4" role="status" style="width: 4rem; height: 4rem;">
            <span class="visually-hidden">Loading...</span>
          </div>

          <h4 class="text-primary mb-3">🏗️ Building Your Adventure...</h4>

          <!-- Progress Bar -->
          <div class="progress mb-4" style="height: 20px; max-width: 400px; margin: 0 auto;">
            <div id="creation-progress-bar" class="progress-bar progress-bar-striped progress-bar-animated"
                 role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
            </div>
          </div>

          <!-- Current Task -->
          <div class="mb-3">
            <h5 id="current-task" class="text-secondary mb-2">🚀 Initializing...</h5>
            <p id="task-description" class="text-muted small">Preparing your adventure</p>
          </div>

          <!-- Step Indicators -->
          <div class="d-flex justify-content-center gap-3 mb-3">
            <div class="text-center">
              <div id="step-characters" class="step-icon mb-1">⏳</div>
              <small class="step-label d-none d-md-block">Characters</small>
            </div>
            <div class="text-center">
              <div id="step-factions" class="step-icon mb-1">⏳</div>
              <small class="step-label d-none d-md-block">Factions</small>
            </div>
            <div class="text-center">
              <div id="step-world" class="step-icon mb-1">⏳</div>
              <small class="step-label d-none d-md-block">World</small>
            </div>
            <div class="text-center">
              <div id="step-story" class="step-icon mb-1">⏳</div>
              <small class="step-label d-none d-md-block">Story</small>
            </div>
          </div>
        </div>
      </div>
    `;

    const container = document.getElementById('campaign-wizard');
    if (container) {
      // CRITICAL FIX: Append spinner instead of replacing entire content
      container.insertAdjacentHTML('beforeend', spinnerHTML);
      // Start progress animation (visual feedback, stops at 90%)
      this.animateCreationProgress();
    }
  }

  animateCreationProgress() {
    const progressBar = document.getElementById('creation-progress-bar');
    const currentTask = document.getElementById('current-task');
    const taskDescription = document.getElementById('task-description');

    if (!progressBar || !currentTask || !taskDescription) return;

    const steps = [
      {
        progress: 20,
        task: '🧙‍♂️ Building characters...',
        description: 'Creating NPCs, allies, and potential party members',
        icon: 'step-characters',
        duration: 20000,
      },
      {
        progress: 40,
        task: '⚔️ Establishing factions...',
        description: 'Designing competing groups, guilds, and political powers',
        icon: 'step-characters',
        duration: 25000,
      },
      {
        progress: 60,
        task: '🌍 Defining world rules...',
        description: 'Setting magic systems, geography, and cultural norms',
        icon: 'step-factions',
        duration: 25000,
      },
      {
        progress: 90,
        task: '📖 Crafting story hook...',
        description: 'Weaving together an engaging opening scenario',
        icon: 'step-world',
        duration: 20000,
      },
    ];

    let currentStep = 0;

    const updateProgress = () => {
      if (currentStep >= steps.length) {
        // Stay at 90% and wait for real completion
        return;
      }

      const step = steps[currentStep];

      // Update progress bar
      progressBar.style.width = `${step.progress}%`;

      // Update text
      currentTask.textContent = step.task;
      taskDescription.textContent = step.description;

      // Update step icons
      if (currentStep > 0) {
        const prevIcon = document.getElementById(steps[currentStep - 1].icon);
        if (prevIcon) prevIcon.textContent = '✅';
      }

      const currentIcon = document.getElementById(step.icon);
      if (currentIcon) currentIcon.textContent = '🔄';

      currentStep++;

      if (currentStep < steps.length) {
        setTimeout(updateProgress, step.duration);
      }
      // When we reach the end, stay at 90% - let real completion handle the final 100%
    };

    // Start progress
    setTimeout(updateProgress, 500);
  }

  completeProgress() {
    const progressBar = document.getElementById('creation-progress-bar');
    const currentTask = document.getElementById('current-task');
    const taskDescription = document.getElementById('task-description');

    if (!progressBar || !currentTask || !taskDescription) return;

    // Jump to 100% when backend actually completes
    progressBar.style.width = '100%';
    currentTask.textContent = '✨ Finalizing adventure...';
    taskDescription.textContent = 'Your world is ready! Launching campaign...';

    // Mark final step as complete
    const finalIcon = document.getElementById('step-story');
    if (finalIcon) finalIcon.textContent = '✅';
  }

  resetWizard() {
    // Remove any existing spinner
    const existingSpinner = document.getElementById(
      'campaign-creation-spinner',
    );
    if (existingSpinner) {
      existingSpinner.remove();
    }

    // Show wizard content and navigation
    const wizardContent = document.querySelector('.wizard-content');
    const wizardNav = document.querySelector('.wizard-navigation');

    if (wizardContent) wizardContent.style.display = 'block';
    if (wizardNav) wizardNav.style.display = 'flex';

    // Reset to step 1
    this.currentStep = 1;

    // Clear form fields
    const titleInput = document.getElementById('wizard-campaign-title');
    const promptInput = document.getElementById('wizard-campaign-prompt');

    if (titleInput) titleInput.value = '';
    if (promptInput) promptInput.value = '';

    // Reset all checkboxes to default (checked)
    const checkboxes = [
      'wizard-mechanics',
      'wizard-companions',
      'wizard-default-world',
    ];

    checkboxes.forEach((id) => {
      const checkbox = document.getElementById(id);
      if (checkbox) checkbox.checked = true;
    });

    // Reset step indicators
    document.querySelectorAll('.step-indicator').forEach((indicator) => {
      indicator.classList.remove('active', 'completed');
    });

    document.querySelectorAll('.wizard-step').forEach((step) => {
      step.classList.remove('active');
    });

    // Activate step 1
    document
      .querySelector('[data-step="1"].step-indicator')
      ?.classList.add('active');
    document
      .querySelector('[data-step="1"].wizard-step')
      ?.classList.add('active');

    // Update UI
    this.updateUI();
    this.updatePreview();
  }

  populateOriginalForm(data) {
    const originalForm = document.getElementById('new-campaign-form');
    if (!originalForm) return;

    // Set basic fields
    const titleInput = originalForm.querySelector('#campaign-title');
    const characterInput = originalForm.querySelector('#character-input');
    const settingInput = originalForm.querySelector('#setting-input');
    const descriptionInput = originalForm.querySelector('#description-input');

    if (titleInput) titleInput.value = data.title;
    if (characterInput) characterInput.value = data.character;
    if (settingInput) settingInput.value = data.setting;
    if (descriptionInput) descriptionInput.value = data.description || '';

    // Campaign type is now determined by description content, not explicit field

    // Set checkboxes
    originalForm
      .querySelectorAll('input[type="checkbox"]')
      .forEach((checkbox) => {
        checkbox.checked = false;
      });

    data.selectedPrompts.forEach((prompt) => {
      const checkbox = originalForm.querySelector(`input[value="${prompt}"]`);
      if (checkbox) checkbox.checked = true;
    });

    data.customOptions.forEach((option) => {
      const checkbox = originalForm.querySelector(`input[value="${option}"]`);
      if (checkbox) checkbox.checked = true;
    });
  }
}

// Initialize campaign wizard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.campaignWizard = new CampaignWizard();
});
