CREATE TABLE results (
tenant_id VARCHAR NOT NULL,
id BIGINT NOT NULL,
device_id UNSIGNED_INT,
collector_id UNSIGNED_INT,
parser_table_id UNSIGNED_INT,
raw VARBINARY, 

# CEF fields
deviceVendor VARCHAR(1023),
deviceProduct VARCHAR(1023),
deviceVersion VARCHAR(255),
signatureId VARCHAR(1023),
name VARCHAR(1023),
severity UNSIGNED_INT,
deviceAction VARCHAR(63),
applicationProtocol VARCHAR(31),
baseEventCount UNSIGNED_INT,
deviceAddress VARCHAR(16),
deviceHostName VARCHAR(1023),
destinationAddress VARCHAR(16),
destinationHostName VARCHAR(1023),
destinationMacAddress VARCHAR(17),
destinationNtDomain VARCHAR(255),
destinationPort UNSIGNED_INT,
destinationProcessName VARCHAR(1023),
destinationUserId VARCHAR(1023),
destinationUserPrivileges VARCHAR(1023),
destinationUserName VARCHAR(1023),
endTime TIMESTAMP,
fileName VARCHAR(1023),
fileSize UNSIGNED_INT,
bytesIn UNSIGNED_INT,
message VARCHAR(1023),
bytesOut UNSIGNED_INT,
transportProtocol VARCHAR(31),
receiptTime TIMESTAMP,
requestURL VARCHAR(1023),
sourceAddress VARCHAR(16),
sourceHostName VARCHAR(1023),
sourceMacAddress VARCHAR(17),
sourceNtDomain VARCHAR(255),
sourcePort UNSIGNED_INT,
sourceUserPrivileges VARCHAR(1023),
sourceUserId VARCHAR(1023),
sourceUserName VARCHAR(1023),
startTime TIMESTAMP,
deviceEventCategory VARCHAR(1023),
deviceCustomString1 VARCHAR(1023),
deviceCustomString2Label VARCHAR(1023),
deviceCustomString2 VARCHAR(1023),
deviceCustomString3Label VARCHAR(1023),
deviceCustomString3 VARCHAR(1023),
deviceCustomString4Label VARCHAR(1023),
deviceCustomString4 VARCHAR(1023),
deviceCustomString5Label VARCHAR(1023),
deviceCustomString5 VARCHAR(1023),
deviceCustomString6Label VARCHAR(1023),
deviceCustomString6 VARCHAR(1023),
deviceCustomNumber1Label VARCHAR(1023),
deviceCustomNumber1 UNSIGNED_INT,
deviceCustomNumber2Label VARCHAR(1023),
deviceCustomNumber2 UNSIGNED_INT,
deviceCustomNumber3Label VARCHAR(1023),
deviceCustomNumber3 UNSIGNED_INT,
deviceCustomDate1Label VARCHAR(1023),
deviceCustomDate1 TIMESTAMP,
deviceCustomDate2Label VARCHAR(1023),
deviceCustomDate2 TIMESTAMP,
deviceNtDomain VARCHAR(255),
deviceDnsDomain VARCHAR(255),
deviceTranslatedAddress VARCHAR(16),
deviceMacAddress VARCHAR(17),
destinationDnsDomain VARCHAR(255),
destinationServiceName VARCHAR(1023),
destinationTranslatedAddress VARCHAR(16),
destinationTranslatedPort UNSIGNED_INT,
deviceDirection VARCHAR(1023),
deviceExternalId VARCHAR(255),
deviceFamily VARCHAR(1023),
deviceInboundInterface VARCHAR(15),
deviceOutboundInterface VARCHAR(15),
deviceProcessName VARCHAR(1023),
externalId UNSIGNED_INT,
fileCreateTime TIMESTAMP,
fileHash VARCHAR(255),
fileId VARCHAR(1023),
fileModificationTime TIMESTAMP,
filePath VARCHAR(1023),
filePermission VARCHAR(1023),
fileType VARCHAR(1023),
oldFileCreateTime TIMESTAMP,
oldFileHash VARCHAR(255),
oldFileId VARCHAR(1023),
oldFileModificationTime TIMESTAMP,
oldFileName VARCHAR(1023),
oldFilePath VARCHAR(1023),
oldFilePermission VARCHAR(1023),
oldFileSize UNSIGNED_INT,
oldFileType VARCHAR(1023),
requestClientApplication VARCHAR(1023),
requestCookies VARCHAR(1023),
requestMethod VARCHAR(1023),
sourceDnsDomain VARCHAR(255),
sourceServiceName VARCHAR(1023),
sourceTranslatedAddress VARCHAR(15),
sourceTranslatedPort UNSIGNED_INT,
CONSTRAINT pk PRIMARY KEY (tenant_id, id))
MULTI_TENANT=true 
