@0xea58bcac2fa96450;

using Cxx = import "/capnp/c++.capnp";
$Cxx.namespace("xboxrc");

struct Xbox @0x8000000000000050
{
	enum EventType {
		none @0;
		button @1;
		axis @2;
	}

	enum EventField {
		none @0;
		lx @1;
		ly @2;
		lz @3;
		rx @4;
		ry @5;
		rz @6;
		hat0x @7;
		hat0y @8;
		a @9;
		b @10;
		x @11;
		y @12;
		tl @13;
		tr @14;
		select @15;
		start @16;
		mode @17;
		thumbl @18;
		thumbr @19;
		dpadUp @20;
		dpadRight @21;
		dpadDown @22;
		dpadLeft @23;		
	}

  timestamp		@0 : UInt64;
  type			@1 : EventType;
  field 		@2 : EventField;
  value 		@3 : Int32;
}
