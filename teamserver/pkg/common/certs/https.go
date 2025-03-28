package certs

// Copied from Silver C2: https://github.com/BishopFox/sliver/blob/master/server/certs/https.go

import (
	"bytes"
	"crypto/ecdsa"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/binary"
	"encoding/pem"
	"fmt"
	"math/big"
	"net"
	"strings"
	"time"

	"Havoc/pkg/logger"

	insecureRand "math/rand"
)

const (
	// HTTPSCA - Directory containing operator certificates
	HTTPSCA = "https"

	// RSAKeySize - Default size of RSA keys in bits
	RSAKeySize = 2048 // This is plenty 4096 is overkill

	// Certs are valid for ~3 Years, minus up to 1 year from Now()
	validFor = 3 * (365 * 24 * time.Hour)

	// ECCKey - Namespace for ECC keys
	ECCKey = "ecc"

	// RSAKey - Namespace for RSA keys
	RSAKey = "rsa"
)

var (
	// State -> Localities -> Street Addresses
	states = map[string]map[string][]string{
		"Alabama": {
			"Birmingham": {"2200 Morris Avenue", "1901 6th Avenue North", "420 20th Street North"},
			"Montgomery": {"600 Dexter Avenue", "300 Water Street", "1 Court Square"},
			"Mobile":     {"165 St. Francis Street", "101 Dauphin Street", "350 Conti Street"},
			"Huntsville": {"700 Monroe Street", "315 Clinton Avenue", "2211 Seminole Drive"},
		},
		"Arizona": {
			"Phoenix":    {"1 E. Washington Street", "455 N. 3rd Street", "2 N. Central Avenue"},
			"Mesa":       {"20 E. Main Street", "1630 S. Stapley Drive", "4050 E. Cotton Center Blvd"},
			"Scottsdale": {"7014 E. Camelback Road", "15029 N. Thompson Peak Parkway", "4343 N. Scottsdale Road"},
			"Chandler":   {"1200 S. Alma School Road", "2680 S. Val Vista Drive", "3075 W. Chandler Blvd"},
			"Tucson":     {"5210 E. Williams Circle", "4280 N. Campbell Avenue", "1 E. Broadway Blvd"},
		},
		"California": {
			"San Francisco": {"One Market Plaza", "101 California Street", "525 Market Street", "Pier 39", "Golden Gate Bridge"},
			"Oakland":       {"1111 Broadway", "555 12th Street", "1000 Broadway"},
			"Berkeley":      {"2150 Shattuck Avenue", "2000 Center Street", "2118 Milvia Street"},
			"Palo Alto":     {"530 Lytton Avenue", "2600 El Camino Real", "101 University Avenue"},
			"Los Angeles":   {"350 S. Grand Avenue", "633 W. 5th Street", "915 Wilshire Blvd"},
			"San Diego":     {"600 B Street", "750 B Street", "101 W. Broadway"},
			"San Jose":      {"60 S. Market Street", "50 W. San Fernando Street", "4 N. Second Street"},
			"Sacramento":    {"1215 K Street", "770 L Street", "980 9th Street"},
		},
		"Colorado": {
			"Denver":           {"1144 15th Street", "1401 Lawrence Street", "1801 California Street"},
			"Boulder":          {"1900 9th Street", "1942 Broadway", "2525 Arapahoe Avenue"},
			"Aurora":           {"14200 E. Alameda Avenue", "15151 E. Alameda Parkway", "15000 E. Mississippi Avenue"},
			"Fort Collins":     {"123 N. College Avenue", "2000 S. College Avenue", "350 Linden Street"},
			"Colorado Springs": {"102 S. Tejon Street", "121 S. Tejon Street", "2424 Garden of the Gods Road"},
		},
		"Connecticut": {
			"New Haven":  {"195 Church Street", "265 Church Street", "555 Long Wharf Drive"},
			"Bridgeport": {"1000 Lafayette Blvd", "144 Golden Hill Street", "350 Fairfield Avenue"},
			"Stamford":   {"1055 Washington Blvd", "177 Broad Street", "300 Atlantic Street"},
			"Norwalk":    {"761 Main Avenue", "50 Washington Street", "605 West Avenue"},
			"Hartford":   {"100 Pearl Street", "20 Church Street", "280 Trumbull Street"},
		},
		"Florida": {
			"Miami":           {"1221 Brickell Avenue", "701 Brickell Avenue", "200 S. Biscayne Blvd"},
			"Orlando":         {"20 N. Orange Avenue", "300 S. Orange Avenue", "800 N. Magnolia Avenue"},
			"Tampa":           {"401 E. Jackson Street", "400 N. Ashley Drive", "501 E. Kennedy Blvd"},
			"Jacksonville":    {"1 Independent Drive", "200 W. Forsyth Street", "225 Water Street"},
			"West Palm Beach": {"777 S. Flagler Drive", "250 S. Australian Avenue", "101 N. Clematis Street"},
		},
		"Georgia": {
			"Atlanta":  {"191 Peachtree Street", "1180 Peachtree Street", "3344 Peachtree Road"},
			"Savannah": {"2 E. Bryan Street", "127 Abercorn Street", "5 W. Broughton Street"},
			"Augusta":  {"1450 Greene Street", "699 Broad Street", "801 Broad Street"},
			"Columbus": {"1000 Broadway", "233 12th Street", "700 Front Avenue"},
		},
		"Illinois": {
			"Chicago":     {"233 S. Wacker Drive", "300 N. LaSalle Street", "71 S. Wacker Drive"},
			"Aurora":      {"175 E. Galena Blvd", "400 S. River Street", "65 Water Street"},
			"Naperville":  {"55 S. Main Street", "100 S. Washington Street", "200 E. 5th Avenue"},
			"Peoria":      {"100 SW Water Street", "401 Main Street", "124 SW Adams Street"},
			"Springfield": {"1 E. Old State Capitol Plaza", "600 E. Adams Street", "700 E. Adams Street"},
		},
		"Massachusetts": {
			"Boston":      {"One Financial Center", "100 Federal Street", "53 State Street"},
			"Cambridge":   {"One Broadway", "10 Canal Park", "245 First Street"},
			"Worcester":   {"370 Main Street", "100 Front Street", "120 Front Street"},
			"Springfield": {"1441 Main Street", "1391 Main Street", "300 State Street"},
		},
		"Michigan": {
			"Detroit":      {"500 Woodward Avenue", "400 Renaissance Center", "150 W. Jefferson Avenue"},
			"Grand Rapids": {"111 Lyon Street NW", "50 Louis Street NW", "250 Monroe Avenue NW"},
			"Ann Arbor":    {"201 S. Main Street", "101 N. Main Street", "2723 S. State Street"},
			"Lansing":      {"124 W. Allegan Street", "215 S. Washington Square", "100 E. Michigan Avenue"},
		},
		"New York": {
			"New York":  {"One World Trade Center", "30 Rockefeller Plaza", "345 Park Avenue", "270 Madison Avenue"},
			"Buffalo":   {"One Seneca Tower", "40 Fountain Plaza", "300 Niagara Street"},
			"Rochester": {"One East Avenue", "100 State Street", "260 East Main Street"},
			"Syracuse":  {"110 W. Fayette Street", "333 W. Washington Street", "100 Clinton Square"},
			"Albany":    {"100 State Street", "41 State Street", "500 Federal Street"},
		},
		"Texas": {
			"Houston":     {"1000 Louisiana Street", "601 Travis Street", "1400 Smith Street"},
			"Dallas":      {"2200 Ross Avenue", "1717 Main Street", "901 Main Street"},
			"Austin":      {"100 Congress Avenue", "303 Colorado Street", "500 W. 2nd Street"},
			"San Antonio": {"112 E. Pecan Street", "300 Convent Street", "700 N. St. Mary's Street"},
			"Fort Worth":  {"100 Throckmorton Street", "301 Commerce Street", "801 Cherry Street"},
		},
		"Washington": {
			"Seattle":  {"1201 Third Avenue", "800 Fifth Avenue", "1000 Second Avenue"},
			"Tacoma":   {"1119 Pacific Avenue", "950 Pacific Avenue", "1501 Pacific Avenue"},
			"Olympia":  {"111 Market Street NE", "400 Capitol Way S", "530 Water Street SW"},
			"Spokane":  {"601 W. Main Avenue", "801 W. Riverside Avenue", "111 N. Post Street"},
			"Bellevue": {"10900 NE 8th Street", "10500 NE 8th Street", "500 108th Avenue NE"},
		},
		"Virginia": {
			"Richmond":       {"1001 E. Cary Street", "901 E. Byrd Street", "1111 E. Main Street"},
			"Norfolk":        {"101 W. Main Street", "150 W. Main Street", "440 Monticello Avenue"},
			"Virginia Beach": {"222 Central Park Avenue", "249 Central Park Avenue", "4500 Main Street"},
			"Alexandria":     {"100 N. Pitt Street", "333 John Carlyle Street", "1800 Diagonal Road"},
		},
	}

	// More realistic organization names by industry
	techOrgNames = []string{
		"Quantum", "Cyber", "Digital", "Global", "Nexus", "Vertex", "Binary", "Vector",
		"Apex", "Echo", "Pulse", "Fusion", "Alpine", "Horizon", "Cipher", "Helios",
		"Onyx", "Radiant", "Spark", "Titan", "Vortex", "Zenith", "Omni", "Matrix",
	}

	techOrgTypes = []string{
		"Systems", "Networks", "Solutions", "Technologies", "Computing", "Innovations",
		"Dynamics", "Communications", "Security", "Analytics", "Data", "Infosystems",
		"Software", "Platforms", "Cybersecurity", "Informatics", "Tech", "Cloud",
	}

	financeOrgNames = []string{
		"Summit", "Meridian", "Pinnacle", "Atlas", "Capital", "Premier", "Legacy", "Sentinel",
		"Strategic", "Liberty", "Heritage", "Monarch", "Commonwealth", "Cornerstone", "Prestige",
		"Vanguard", "Sterling", "Prosperity", "Guardian", "Dominion", "Alliance", "Sovereign",
	}

	financeOrgTypes = []string{
		"Financial", "Investments", "Advisors", "Partners", "Asset Management", "Associates",
		"Capital", "Equity", "Holdings", "Wealth", "Banking", "Trust", "Finance", "Group",
		"Securities", "Bank", "Credit", "Funding", "Ventures",
	}

	healthOrgNames = []string{
		"Aurora", "Beacon", "Cascade", "Integra", "Nova", "Solaris", "Vital", "Ascent",
		"Essence", "Genesis", "Lumina", "Pinnacle", "Unity", "Wellness", "Harmony", "Remedy",
		"Optimal", "Providence", "Renewal", "Serenity", "Tranquility", "Vivant",
	}

	healthOrgTypes = []string{
		"Health", "Medical", "Healthcare", "Clinic", "Wellness", "Life Sciences", "Therapeutics",
		"Pharmaceuticals", "Laboratories", "Biotech", "Care", "Research", "Diagnostics", "Health Partners",
		"Medicine", "Health Services", "Medical Center", "Health Systems",
	}

	generalOrgNames = []string{
		"Central", "Dynamic", "Everest", "Frontier", "Insight", "Metro", "National", "Precision",
		"Premium", "Quality", "Regional", "Reliable", "Select", "Standard", "Superior", "United",
		"Universal", "Urban", "Western", "Eastern", "Northern", "Southern", "Pacific", "Atlantic",
	}

	generalOrgTypes = []string{
		"Industries", "Corporation", "Enterprises", "Company", "Services", "Products", "International",
		"Incorporated", "Business Solutions", "Management", "Logistics", "Operations", "Resources",
		"Development", "Agency", "Consultants", "Associates", "Global", "Worldwide",
	}

	orgSuffixes = []string{
		"Inc", "LLC", "Corp", "Ltd", "Co", "Group", "Holdings", "Incorporated", "Limited",
		"Corporation", "International", "Enterprises", "Associates", "Partners", "Services",
		"Solutions", "Systems", "Technologies", "Networks", "Global", "Worldwide", "America",
	}

	// Domain TLDs for email domains
	tldList = []string{
		"com", "net", "org", "io", "co", "tech", "solutions", "group", "info",
		"systems", "network", "cloud", "digital", "global", "app", "dev",
	}
)

func randomState() string {
	keys := make([]string, 0, len(states))
	for k := range states {
		keys = append(keys, k)
	}
	return keys[insecureRand.Intn(len(keys))]
}

func randomLocality(state string) string {
	locales := states[state]
	keys := make([]string, 0, len(locales))
	for k := range locales {
		keys = append(keys, k)
	}
	return keys[insecureRand.Intn(len(keys))]
}

func randomStreetAddress(state string, locality string) string {
	addresses := states[state][locality]
	return addresses[insecureRand.Intn(len(addresses))]
}

func randomProvinceLocalityStreetAddress() ([]string, []string, []string) {
	state := randomState()
	locality := randomLocality(state)
	streetAddress := randomStreetAddress(state, locality)
	return []string{state}, []string{locality}, []string{streetAddress}
}

func randomPostalCode() []string {
	// Generate more realistic US ZIP codes
	switch insecureRand.Intn(10) {
	case 0:
		// 5-digit ZIP code
		return []string{fmt.Sprintf("%05d", insecureRand.Intn(90000)+10000)}
	case 1:
		// ZIP+4 format
		return []string{fmt.Sprintf("%05d-%04d", insecureRand.Intn(90000)+10000, insecureRand.Intn(10000))}
	default:
		// Skip postal code sometimes
		return []string{}
	}
}

func randomOrganizationUnit() []string {
	// Randomly decide whether to include an organizational unit
	if insecureRand.Intn(4) == 0 {
		units := []string{
			"Information Technology", "Information Security", "IT Operations", "Engineering",
			"Development", "Research", "Infrastructure", "Operations", "Network Operations",
			"Security Operations", "Technology", "Product Development", "Software Development",
			"DevOps", "Cloud Infrastructure", "Corporate IT", "Enterprise Security",
		}
		return []string{units[insecureRand.Intn(len(units))]}
	}
	return []string{}
}

func generateRandomDomain() string {
	namePool := [][]string{techOrgNames, financeOrgNames, healthOrgNames, generalOrgNames}
	typePool := [][]string{techOrgTypes, financeOrgTypes, healthOrgTypes, generalOrgTypes}

	// Choose a random industry category
	categoryIndex := insecureRand.Intn(len(namePool))
	namesList := namePool[categoryIndex]
	typesList := typePool[categoryIndex]

	name := strings.ToLower(namesList[insecureRand.Intn(len(namesList))])
	orgType := strings.ToLower(typesList[insecureRand.Intn(len(typesList))])

	// Generate domain name formats with various patterns
	switch insecureRand.Intn(5) {
	case 0:
		return name + "." + tldList[insecureRand.Intn(len(tldList))]
	case 1:
		return name + orgType + "." + tldList[insecureRand.Intn(len(tldList))]
	case 2:
		return name + "-" + orgType + "." + tldList[insecureRand.Intn(len(tldList))]
	case 3:
		return orgType + "-" + name + "." + tldList[insecureRand.Intn(len(tldList))]
	default:
		return name + orgType[0:3] + "." + tldList[insecureRand.Intn(len(tldList))]
	}
}

func randomSubject(commonName string) *pkix.Name {
	province, locale, street := randomProvinceLocalityStreetAddress()

	return &pkix.Name{
		Organization:       randomOrganization(),
		OrganizationalUnit: randomOrganizationUnit(),
		Country:            []string{"US"},
		Province:           province,
		Locality:           locale,
		StreetAddress:      street,
		PostalCode:         randomPostalCode(),
		CommonName:         commonName,
	}
}

func randomOrganization() []string {
	// Choose a random industry category
	categoryIndex := insecureRand.Intn(4)
	var orgName, orgType string

	switch categoryIndex {
	case 0:
		orgName = techOrgNames[insecureRand.Intn(len(techOrgNames))]
		orgType = techOrgTypes[insecureRand.Intn(len(techOrgTypes))]
	case 1:
		orgName = financeOrgNames[insecureRand.Intn(len(financeOrgNames))]
		orgType = financeOrgTypes[insecureRand.Intn(len(financeOrgTypes))]
	case 2:
		orgName = healthOrgNames[insecureRand.Intn(len(healthOrgNames))]
		orgType = healthOrgTypes[insecureRand.Intn(len(healthOrgTypes))]
	default:
		orgName = generalOrgNames[insecureRand.Intn(len(generalOrgNames))]
		orgType = generalOrgTypes[insecureRand.Intn(len(generalOrgTypes))]
	}

	// Add a suffix sometimes
	var suffix string
	if insecureRand.Intn(3) > 0 { // 2/3 chance to add a suffix
		suffix = orgSuffixes[insecureRand.Intn(len(orgSuffixes))]
	}

	// Format the organization name with different patterns
	switch insecureRand.Intn(5) {
	case 0:
		return []string{orgName + " " + orgType}
	case 1:
		return []string{orgName + " " + orgType + " " + suffix}
	case 2:
		return []string{orgName + " " + suffix}
	case 3:
		return []string{orgType + " " + orgName + " " + suffix}
	default:
		return []string{orgName + " " + orgType}
	}
}

func publicKey(priv interface{}) interface{} {
	switch k := priv.(type) {
	case *rsa.PrivateKey:
		return &k.PublicKey
	case *ecdsa.PrivateKey:
		return &k.PublicKey
	default:
		return nil
	}
}

func randomInt(max int) int {
	buf := make([]byte, 4)
	rand.Read(buf)
	i := binary.LittleEndian.Uint32(buf)
	return int(i) % max
}

func pemBlockForKey(priv interface{}) *pem.Block {
	switch key := priv.(type) {
	case *rsa.PrivateKey:
		data := x509.MarshalPKCS1PrivateKey(key)
		return &pem.Block{Type: "RSA PRIVATE KEY", Bytes: data}
	case *ecdsa.PrivateKey:
		data, err := x509.MarshalECPrivateKey(key)
		if err != nil {
			logger.Fatal(fmt.Sprintf("Unable to marshal ECDSA private key: %v", err))
		}
		return &pem.Block{Type: "EC PRIVATE KEY", Bytes: data}
	default:
		return nil
	}
}

func generateCertificate(caType string, subject pkix.Name, isCA bool, isClient bool, privateKey interface{}) ([]byte, []byte) {

	// Valid times, subtract random days from .Now()
	notBefore := time.Now()
	days := randomInt(365) * -1 // Within -1 year
	notBefore = notBefore.AddDate(0, 0, days)
	notAfter := notBefore.Add(validFor)
	logger.Debug(fmt.Sprintf("Valid from %v to %v", notBefore, notAfter))

	// Serial number
	serialNumberLimit := new(big.Int).Lsh(big.NewInt(1), 128)
	serialNumber, _ := rand.Int(rand.Reader, serialNumberLimit)
	logger.Debug(fmt.Sprintf("Serial Number: %d", serialNumber))

	var keyUsage = x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature
	var extKeyUsage []x509.ExtKeyUsage

	if isCA {
		logger.Debug("Authority certificate")
		keyUsage = x509.KeyUsageCertSign | x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature
		extKeyUsage = []x509.ExtKeyUsage{
			x509.ExtKeyUsageServerAuth,
			x509.ExtKeyUsageClientAuth,
		}
	} else if isClient {
		logger.Debug("Client authentication certificate")
		extKeyUsage = []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}
	} else {
		logger.Debug("Server authentication certificate")
		extKeyUsage = []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}
	}
	logger.Debug(fmt.Sprintf("ExtKeyUsage = %v", extKeyUsage))

	// Certificate template
	template := x509.Certificate{
		SerialNumber:          serialNumber,
		Subject:               subject,
		NotBefore:             notBefore,
		NotAfter:              notAfter,
		KeyUsage:              keyUsage,
		ExtKeyUsage:           extKeyUsage,
		BasicConstraintsValid: isCA,
	}

	if !isClient {
		// Host or IP address
		if ip := net.ParseIP(subject.CommonName); ip != nil {
			logger.Debug(fmt.Sprintf("Certificate authenticates IP address: %v", ip))
			template.IPAddresses = append(template.IPAddresses, ip)
		} else {
			logger.Debug(fmt.Sprintf("Certificate authenticates host: %v", subject.CommonName))
			template.DNSNames = append(template.DNSNames, subject.CommonName)

			// Add some additional subject alternative names for more realistic certificates
			if insecureRand.Intn(2) == 0 {
				// Add 1-3 additional domain names
				for i := 0; i < insecureRand.Intn(3)+1; i++ {
					altDomain := generateRandomDomain()
					template.DNSNames = append(template.DNSNames, altDomain)
					logger.Debug(fmt.Sprintf("Added alternative domain name: %v", altDomain))
				}
			}
		}
	} else {
		logger.Debug(fmt.Sprintf("Client certificate authenticates CN: %v", subject.CommonName))
	}

	// Sign certificate or self-sign if CA
	var certErr error
	var derBytes []byte

	if isCA {
		logger.Debug("Certificate is an AUTHORITY")
		template.IsCA = true
		template.KeyUsage |= x509.KeyUsageCertSign
		derBytes, certErr = x509.CreateCertificate(rand.Reader, &template, &template, publicKey(privateKey), privateKey)
	}

	if certErr != nil {
		// We maybe don't want this to be fatal, but it should basically never happen afaik
		logger.Fatal(fmt.Sprintf("Failed to create certificate: %s", certErr.Error()))
	}

	// Encode certificate and key
	certOut := bytes.NewBuffer([]byte{})
	pem.Encode(certOut, &pem.Block{Type: "CERTIFICATE", Bytes: derBytes})

	keyOut := bytes.NewBuffer([]byte{})
	pem.Encode(keyOut, pemBlockForKey(privateKey))

	return certOut.Bytes(), keyOut.Bytes()
}

// HTTPSGenerateRSACertificate - Generate a server certificate signed with a given CA
func HTTPSGenerateRSACertificate(host string) ([]byte, []byte, error) {
	logger.Debug(fmt.Sprintf("Generating TLS certificate (RSA) for '%s' ...", host))

	var privateKey interface{}
	var err error

	// Generate private key
	privateKey, err = rsa.GenerateKey(rand.Reader, RSAKeySize)
	if err != nil {
		logger.Debug("Failed to generate private key: " + err.Error())
		return nil, nil, err
	}
	subject := randomSubject(host)
	cert, key := generateCertificate(HTTPSCA, (*subject), true, false, privateKey)
	// err = saveCertificate(HTTPSCA, RSAKey, host, cert, key)
	return cert, key, err
}
