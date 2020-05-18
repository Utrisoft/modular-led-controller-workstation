from audioled import modulation, project, serverconfiguration, version, client_config
from audioled_controller import sysex_data

from pyupdater.client import Client
import mido
import logging
import os
import json
import jsonpickle
import zlib
logger = logging.getLogger(__name__)

controllerMap = {
    1: modulation.CTRL_MODULATION,  # mod wheel
    7: modulation.CTRL_BRIGHTNESS,  # volume
    11: modulation.CTRL_INTENSITY,  # expression
    21: modulation.CTRL_SPEED,  # unknown param?
    30: modulation.CTRL_PRIMARY_COLOR_R,
    31: modulation.CTRL_PRIMARY_COLOR_G,
    32: modulation.CTRL_PRIMARY_COLOR_B,
    40: modulation.CTRL_SECONDARY_COLOR_R,
    41: modulation.CTRL_SECONDARY_COLOR_G,
    42: modulation.CTRL_SECONDARY_COLOR_B
}
inverseControllerMap = {}
for k, v in controllerMap.items():
    inverseControllerMap[v] = k

# Helper to convert to json
def _ctrlToValue(ctrl, val):
    if ctrl == modulation.CTRL_PRIMARY_COLOR_R or ctrl == modulation.CTRL_SECONDARY_COLOR_R:
        return {"controllerAmount": 1., "r": val * 255}
    elif ctrl == modulation.CTRL_PRIMARY_COLOR_G or ctrl == modulation.CTRL_SECONDARY_COLOR_G:
        return {"controllerAmount": 1., "g": val * 255}
    elif ctrl == modulation.CTRL_PRIMARY_COLOR_B or ctrl == modulation.CTRL_SECONDARY_COLOR_B:
        return {"controllerAmount": 1., "b": val * 255}
    else:
        return {"controllerAmount": val}

class PathAndUrlDownloader:

    def __init__(self, callback, filename, urls, **kwargs):
        self.filename = filename
        self.urls = urls
        self.hexdigest = kwargs.get("hexdigest")
        self._callback = callback
        logger.debug("Downloader for {}".format(filename))

        self._data = None

    def download_verify_return(self):
        # Download the data from the endpoint and return
        logger.info("Download request for {} received".format(self.filename))
        if self._callback is not None:
            self._data = self._callback(self.filename)
        return self._data

    def download_verify_write(self):
        if self._data is None:
            self._data = self.download_verify_return()
        # Write the downloaded data to the current dir
        logger.info("Write request for {} received".format(self.filename))
        logger.info("Writing {} bytes to file {}".format(len(self._data), self.filename))
        with open(self.filename, 'wb') as f:
            f.write(self._data)

def print_status_info(info):
    total = info.get(u'total')
    downloaded = info.get(u'downloaded')
    status = info.get(u'status')
    logger.info("{}: {} of {} downloaded".format(status, downloaded, total))

class MidiProjectControllerOptions:
    def __init__(self):
        self.update_paths = None
        self.client_config = None

class MidiProjectController:

    def __init__(self, callback=None, options=None):
        self._sendMidiCallback = callback

        self._update_paths = None
        self._client_config = None
        if options is not None:
            self._update_paths = options.update_paths
            self._client_config = options.client_config
        # Client for pyupdate
        if self._client_config is None:
            self._client_config = client_config.ClientConfig()
        self.client = Client(self._client_config, downloader=self.createDownloader)
        self.client.add_progress_hook(print_status_info)

    def createDownloader(self, filename, urls, **kwargs):
        logger.info("Create downloader for {}".format(filename))
        d = PathAndUrlDownloader(self.downloadCallback, filename, urls)
        return d

    def downloadCallback(self, file):
        logger.info("Callback! {}".format(file))
        if self._update_paths is not None:
            for updatePath in self._update_paths:
                logger.info("Checking directory {}".format(updatePath))
                path = os.path.join(updatePath, file)
                if os.path.isfile(path):
                    return open(path, "rb").read()
        logger.error("{} not found".format(file))
        return None

    def handleMidiMsg(self, msg: mido.Message, serverconfig: serverconfiguration.ServerConfiguration, proj: project.Project):
        # of type mido.Message
        # channel	0..15	0
        # frame_type	0..7	0
        # frame_value	0..15	0
        # control	0..127	0
        # note	0..127	0
        # program	0..127	0
        # song	0..127	0
        # value	0..127	0
        # velocity	0..127	64
        # data	(0..127, 0..127, …)	() (empty tuple)
        # pitch	-8192..8191	0
        # pos	0..16383	0
        # time	any integer or float	0

        if msg.type == 'program_change':
            self._handleProgramChange(msg.program, proj)
        elif msg.type == 'control_change':
            self._handleControlChange(msg.control, msg.value, proj)
        elif msg.type == 'sysex':
            self._handleSysex(msg.data, serverconfig, proj)

    def _handleSysex(self, data, serverconfig: serverconfiguration.ServerConfiguration, proj: project.Project):
        if len(data) < 2:
            logger.error("Sysex message too short")
            return

        # logger.info("MIDI-BLE REQ!")
        
        if data[0] == 0x00 and data[1] == 0x00:
            # Version
            logger.info("MIDI-BLE REQ Version")
            if self._sendMidiCallback is not None:
                self._sendMidiCallback(self._createVersionMsg())
        elif data[0] == 0x00 and data[1] == 0x10:
            # Update
            logger.info("MIDI-BLE REQ Update")
            logger.info("Checking for update, current version is {}".format(version.get_version()))
            self.client.refresh()
            app_update = self.client.update_check('Molecole', version.get_version())
            if app_update is not None:
                logger.info("Update {} available".format(app_update.current_version))
                app_update.download()
                logger.info("Update downloaded")
                if app_update.is_downloaded():
                    logger.debug("Extracting update")
                    if app_update.extract():
                        logger.debug("Extract succeeded")
                    else:
                        logger.debug("Extract not successful")
                    # TODO: perform update
            else:
                logger.info("Update check returned no update")
                if self._sendMidiCallback is not None:
                    self._sendMidiCallback(self._createUpdateNotAvailableMsg())
        elif data[0] == 0x00 and data[1] == 0x11:
            # Update check
            logger.info("MIDI-BLE REQ Update check")
            self.client.refresh()
            logger.info("Checking for update {}".format(version.get_version()))
            app_update = self.client.update_check('Molecole', version.get_version())
            if app_update is not None:
                logger.info("Update {} available".format(app_update.version))
                if self._sendMidiCallback is not None:
                    self._sendMidiCallback(self._createUpdateVersionAvailableMsg(app_update.version))
            else:
                logger.info("Update check returned no update")
                if self._sendMidiCallback is not None:
                    self._sendMidiCallback(self._createUpdateNotAvailableMsg())
        elif data[0] == 0x00 and data[1] == 0x20:
            # Active project metadata
            if self._sendMidiCallback is not None:
                metadata = serverconfig.getProjectMetadata(proj.id)
                self._sendMidiCallback(self._createActiveProjectMsg(metadata))
        elif data[0] == 0x00 and data[1] == 0x30:
            # Get projects
            if self._sendMidiCallback is not None:
                metadata = serverconfig.getProjectsMetadata()
                self._sendMidiCallback(self._createProjectsMsg(metadata))
        elif data[0] == 0x00 and data[1] == 0x40:
            # Activate project
            projUid = str(bytes(sysex_data.decode(data[2:])), encoding='utf8')
            logger.info("MIDI-BLE REQ Activate project {}".format(projUid))
            proj = serverconfig.getProject(projUid)
            if proj is not None:
                if self._sendMidiCallback is not None:
                    self._sendMidiCallback(self._createActivateProjSuccessfulMsg())
            else:
                if self._sendMidiCallback is not None:
                    self._sendMidiCallback(self._createActivateProjNotFoundMsg())
        elif data[0] == 0x00 and data[1] == 0x50:
            # Import project
            logger.info("MIDI-BLE REQ Import project")
            projJson = str(bytes(sysex_data.decode(data[2:])), encoding='utf8')
            try:
                serverconfig.importProject(projJson)
                if self._sendMidiCallback is not None:
                    self._sendMidiCallback(self._createImportProjSuccessfulMsg())
            except Exception:
                if self._sendMidiCallback is not None:
                    self._sendMidiCallback(self._createImportProjErrorMsg())
        elif data[0] == 0x00 and data[1] == 0x60:
            # Export project
            byteArr = bytes(sysex_data.decode(data[2:]))
            logger.debug("Decoded {} to {}".format([hex(c) for c in data[2:]], byteArr))
            projUid = str(byteArr, encoding='utf8')
            logger.info("MIDI-BLE REQ Export project {}".format(projUid))
            proj = serverconfig.getProject(projUid)
            if proj is not None:
                if self._sendMidiCallback is not None:
                    self._sendMidiCallback(self._createExportProjSuccessfulMsg(proj))
            else:
                if self._sendMidiCallback is not None:
                    self._sendMidiCallback(self._createExportProjNotFoundMsg())
        else:
            logger.error("MIDI-BLE Unknown sysex {} {}".format(hex(data[0]), hex(data[1])))

    def _createExportProjSuccessfulMsg(self, proj):
        logger.info("MIDI-BLE RESPONSE Export project - Successful")
        projJson = jsonpickle.dumps(proj)
        projGzip = zlib.compress(bytes(projJson, encoding='utf8'))
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x60] + sysex_data.encode(projGzip)
        return sendMsg
    
    def _createExportProjNotFoundMsg(self):
        logger.info("MIDI-BLE RESPONSE Export project - Not found")
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x6F]
        return sendMsg

    def _createImportProjSuccessfulMsg(self):
        logger.info("MIDI-BLE RESPONSE Import project - Successful")
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x50]
        return sendMsg

    def _createImportProjErrorMsg(self):
        logger.info("MIDI-BLE RESPONSE Import project - Error")
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x5F]
        return sendMsg

    def _createActivateProjSuccessfulMsg(self):
        logger.info("MIDI-BLE RESPONSE Activate project - Successful")
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x40]
        return sendMsg
    
    def _createActivateProjNotFoundMsg(self):
        logger.info("MIDI-BLE RESPONSE Activate project - Project not found")
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x4F]
        return sendMsg

    def _createUpdateVersionAvailableMsg(self, version):
        logger.info("MIDI-BLE RESPONSE Update to version {} available".format(version))
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x11] + sysex_data.encode(version)
        return sendMsg

    def _createUpdateNotAvailableMsg(self):
        logger.info("MIDI-BLE RESPONSE No update available")
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x1F]
        return sendMsg
    
    def _createActiveProjectMsg(self, metadata):
        data = json.dumps(metadata)
        logger.info("MIDI-BLE RESPONSE Active project {}".format(data))
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x20] + sysex_data.encode(data)
        return sendMsg

    def _createProjectsMsg(self, metadata):
        data = json.dumps(metadata)
        logger.info("MIDI-BLE RESPONSE project metadata: {}".format(data))
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x30] + sysex_data.encode(data)
        return sendMsg

    def _createVersionMsg(self):
        v = version.get_version()
        logger.info("MIDI-BLE RESPONSE Current Version {}".format(v))
        sendMsg = mido.Message('sysex')
        sendMsg.data = [0x00, 0x00] + sysex_data.encode(v)
        return sendMsg

    def _handleProgramChange(self, program, proj):
        proj.activateScene(program)

        # Send current midi controller status
        status = proj.getControllerModulations()
        for controller, v in status.items():
            logger.info("Sending modulation controller value {} for controller {}".format(v, controller))
            sendMsg = mido.Message('control_change')
            if controller in inverseControllerMap:
                sendMsg.channel = 1
                sendMsg.control = inverseControllerMap[controller]
                if sendMsg.control >= 30:
                    # scale color data
                    sendMsg.value = int(v / 255 * 127)
                else:
                    sendMsg.value = int(v * 127)
                if self._sendMidiCallback is not None:
                    self._sendMidiCallback(sendMsg)

        # TODO: Send sysex for available controller
        status = proj.getController()
        controllerEnabled = {}
        for controller in modulation.allController:
            if controller in inverseControllerMap:
                controllerEnabled[inverseControllerMap[controller]] = False

        logger.info("Status: {}".format(status.keys()))
        for controller in status.keys():
            if controller in inverseControllerMap:
                controllerEnabled[inverseControllerMap[controller]] = True
        # Create midi message from map
        # TODO: Problem with receiving sysex in JUCE?
        # [StartOfExclusive, ID of vendor (non-commercial in this case), ... data ]
        if True:
            sysexData = [0xF0, 0x7D]
            for controllerNumber, enabled in controllerEnabled.items():
                sysexData += [controllerNumber, (0 if not enabled else 1)]
            sysexData += [0xF7]  # End of exclusive
            logger.info("Sending sysex {}".format(sysexData))
            sysexMsg = mido.Message.from_bytes(sysexData)
            if self._sendMidiCallback is not None:
                self._sendMidiCallback(sysexMsg)
        # Version using note on / note off commands
        for controllerNumber, enabled in controllerEnabled.items():
            msg = None
            if enabled:
                msg = mido.Message('note_on')
            else:
                msg = mido.Message('note_off')
            msg.channel = 1
            msg.note = controllerNumber
            if self._sendMidiCallback is not None:
                self._sendMidiCallback(msg)

        # TODO: Send brightness
        # brightness = proj.getBrightness() # TODO: Implement
        # sendMsg = mido.Message('control_change')
        # sendMsg.channel = 1
        # sendMsg.control = 7
        # sendMsg.value = brightness * 127
        # midiBluetooth.sendMidi(sendMsg)
    
    def _handleControlChange(self, ctrl, value, proj):
        if ctrl in controllerMap:
            controlMsg = controllerMap[ctrl]
            controlVal = _ctrlToValue(controlMsg, value / 127)
            logger.debug("Propagating control change message")
            if controlMsg == modulation.CTRL_BRIGHTNESS:
                # Handle brightness globally
                proj.setBrightness(value / 127)
            else:
                proj.updateModulationSourceValue(0xFFF, controlMsg, controlVal)
        else:
            logger.warn("Unknown controller {}".format(ctrl))
